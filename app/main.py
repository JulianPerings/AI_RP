"""CLI entry point — the main game loop."""

from __future__ import annotations

import argparse
import sys

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

from app.config import CAMPAIGNS_DIR, get_llm_config, DEFAULT_PROVIDER, LLMProvider
from agents.gamemaster import GameMasterAgent
from models.world_state import WorldState
from services.state_manager import StateManager
from services.save_manager import SaveManager
from services.llm_service import LLMService
from services.logger import setup_logging

console = Console()


def _pick_campaign() -> str:
    """List available campaigns and let the player choose one."""
    yamls = sorted(CAMPAIGNS_DIR.glob("*.yaml")) + sorted(CAMPAIGNS_DIR.glob("*.yml"))
    if not yamls:
        console.print("[red]No campaigns found in data/campaigns/.[/red]")
        sys.exit(1)

    console.print("\n[bold]Available Campaigns:[/bold]")
    for i, path in enumerate(yamls, 1):
        console.print(f"  {i}. {path.stem}")

    choice = Prompt.ask(
        "Select a campaign",
        choices=[str(i) for i in range(1, len(yamls) + 1)],
        default="1",
    )
    return str(yamls[int(choice) - 1])


def _pick_provider() -> LLMProvider:
    """Let the player choose an LLM provider at startup."""
    providers: list[LLMProvider] = ["openai", "xai", "gemini"]
    console.print("\n[bold]LLM Providers:[/bold]")
    for i, p in enumerate(providers, 1):
        cfg = get_llm_config(p)
        key_status = "[green]key set[/green]" if cfg.api_key else "[red]no key[/red]"
        default_tag = " [dim](default)[/dim]" if p == DEFAULT_PROVIDER else ""
        console.print(f"  {i}. {p} — {cfg.model} ({key_status}){default_tag}")

    choice = Prompt.ask(
        "Select provider",
        choices=[str(i) for i in range(1, len(providers) + 1)],
        default=str(providers.index(DEFAULT_PROVIDER) + 1),
    )
    return providers[int(choice) - 1]


def _show_banner(provider: LLMProvider, model: str, debug: bool) -> None:
    debug_tag = " [bold red]DEBUG MODE[/bold red]" if debug else ""
    console.print(
        Panel(
            f"[bold magenta]AI RPG[/bold magenta]{debug_tag}\n"
            "A narrative-driven AI adventure.\n"
            f"Provider: [bold]{provider}[/bold] | Model: [bold]{model}[/bold]\n"
            "Type your actions in plain English. Type [bold]quit[/bold] to exit.\n"
            "Commands: [bold]status[/bold] | [bold]inventory[/bold] | [bold]save[/bold] | [bold]debug[/bold] | [bold]quit[/bold]",
            expand=False,
        )
    )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="AI RPG — narrative-driven AI adventure")
    parser.add_argument(
        "--debug", action="store_true",
        help="Enable debug mode: logs all agent ↔ LLM traffic to console and logs/",
    )
    parser.add_argument(
        "--provider", type=str, choices=["openai", "xai", "gemini"],
        help="LLM provider to use (skips interactive selection)",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    debug = args.debug
    setup_logging(debug=debug)

    # --- Provider selection ---------------------------------------------------
    if args.provider:
        provider: LLMProvider = args.provider  # type: ignore[assignment]
    else:
        provider = _pick_provider()

    llm_config = get_llm_config(provider)
    _show_banner(provider, llm_config.model, debug)

    # --- Setup ---------------------------------------------------------------
    campaign_path = _pick_campaign()
    llm = LLMService(provider=provider)
    save_manager = SaveManager()

    # Load or create world state
    world = save_manager.load_latest() or WorldState.from_campaign(campaign_path)
    state_mgr = StateManager(world)

    # Boot GM agent
    gm = GameMasterAgent(llm=llm, state_manager=state_mgr)

    # Opening narration
    opening = gm.begin_adventure()
    console.print(f"\n[bold green]GM:[/bold green] {opening}\n")

    # --- Game loop -----------------------------------------------------------
    while True:
        try:
            player_input = Prompt.ask("[bold cyan]You[/bold cyan]")
        except (KeyboardInterrupt, EOFError):
            player_input = "quit"

        if player_input.strip().lower() in ("quit", "exit", "q"):
            save_manager.save(world)
            console.print("[dim]Game saved. Farewell, adventurer![/dim]")
            break

        if player_input.strip().lower() == "status":
            state_mgr.print_status(console)
            continue

        if player_input.strip().lower() == "inventory":
            state_mgr.print_inventory(console)
            continue

        if player_input.strip().lower() == "save":
            save_manager.save(world)
            console.print("[dim]Game saved.[/dim]")
            continue

        if player_input.strip().lower() == "debug":
            debug = not debug
            setup_logging(debug=debug)
            state = "[bold green]ON[/bold green]" if debug else "[bold red]OFF[/bold red]"
            console.print(f"[dim]Debug mode: {state}[/dim]")
            if debug:
                console.print("[dim]Agent ↔ LLM traffic will appear in stderr and logs/[/dim]")
            continue

        # Send action to GM
        response = gm.process_action(player_input)
        console.print(f"\n[bold green]GM:[/bold green] {response}\n")

        # Auto-save periodically
        if world.turn_count % 5 == 0:
            save_manager.save(world)


if __name__ == "__main__":
    main()
