"""GameMaster agent — orchestrates the game, narrates, delegates to sub-agents."""

from __future__ import annotations

import json
from typing import Any

from agents.base_agent import BaseAgent
from agents.npc_agent import NPCAgent
from models.action import Action, ActionType
from services import dice as dice_engine
from services.llm_service import LLMService
from services.memory_manager import MemoryManager
from services.state_manager import StateManager


class GameMasterAgent(BaseAgent):
    """The central orchestrator of the AI RPG."""

    prompt_file = "gamemaster.md"

    def __init__(
        self,
        llm: LLMService,
        state_manager: StateManager,
        **kwargs: Any,
    ) -> None:
        super().__init__(llm, **kwargs)
        self.state = state_manager
        self.memory_mgr = MemoryManager(llm)
        self._npc_agents: dict[str, NPCAgent] = {}

    # ------------------------------------------------------------------
    # Context building
    # ------------------------------------------------------------------

    def _build_context(self) -> str:
        """Assemble the current world context injected into every GM call."""
        w = self.state.world
        p = w.player
        parts: list[str] = []

        # Location
        parts.append(f"## Current Location\n{w.current_location or 'Unknown'}")

        # Player summary
        parts.append(
            f"## Player\n"
            f"Name: {p.name} | HP: {p.current_hp}/{p.max_hp} | Level: {p.level}\n"
            f"STR {p.stats.strength.total} | AGI {p.stats.agility.total} | "
            f"MND {p.stats.mind.total} | CHA {p.stats.charisma.total}\n"
            f"Gold: {p.gold}"
        )

        # Inventory
        if p.inventory:
            item_names = [
                w.items[iid].name if iid in w.items else iid for iid in p.inventory
            ]
            parts.append(f"## Inventory\n{', '.join(item_names)}")

        # Nearby NPCs
        nearby = self.state.get_npcs_at_location(w.current_location)
        if nearby:
            npc_list = ", ".join(f"{n.name} ({n.id})" for n in nearby)
            parts.append(f"## Nearby NPCs\n{npc_list}")

        # Active quests
        active = [q for q, done in w.quest_flags.items() if not done]
        if active:
            parts.append(f"## Active Quests\n{', '.join(active)}")

        # Recent narrative (last 5)
        if w.narrative_log:
            recent = w.narrative_log[-5:]
            parts.append(f"## Recent Events\n" + "\n".join(f"- {e}" for e in recent))

        return "\n\n".join(parts)

    # ------------------------------------------------------------------
    # Response parsing
    # ------------------------------------------------------------------

    def _parse_gm_response(self, raw: str) -> dict[str, Any]:
        """Try to parse JSON from the GM response. Fall back to plain narrative."""
        # Strip markdown code fences if present
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            # Remove first and last fence lines
            lines = [l for l in lines if not l.strip().startswith("```")]
            cleaned = "\n".join(lines).strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            return {"narrative": raw, "actions": [], "mechanical_notes": ""}

    # ------------------------------------------------------------------
    # Action processing
    # ------------------------------------------------------------------

    def _process_actions(self, actions: list[dict[str, Any]]) -> list[str]:
        """Execute structured actions and return mechanical notes."""
        notes: list[str] = []

        for act_data in actions:
            action_type = act_data.get("action_type", "narrate")
            target = act_data.get("target", "")
            details = act_data.get("details", {})

            if action_type == "move":
                self.state.move_player(target)
                notes.append(f"Moved to {target}.")

            elif action_type == "update_inventory":
                for item_id in details.get("add", []):
                    self.state.add_item(item_id)
                    notes.append(f"Acquired {item_id}.")
                for item_id in details.get("remove", []):
                    self.state.remove_item(item_id)
                    notes.append(f"Lost {item_id}.")

            elif action_type == "update_relationship":
                delta = details.get("delta", 0)
                note = details.get("note", "")
                self.state.adjust_relationship(target, delta, note)
                notes.append(f"Relationship with {target} shifted by {delta}.")

            elif action_type == "skill_check":
                stat = details.get("stat", "strength")
                dc = details.get("difficulty", 10)
                skill = details.get("skill", "")
                success, result = dice_engine.skill_check(
                    self.state.player, stat, dc, skill
                )
                notes.append(result.detail)

            elif action_type == "combat_attack":
                stat_name = details.get("stat", "strength")
                stat = self.state.player.stats.get(stat_name)
                defender_ac = details.get("defender_ac", 5)
                weapon_dmg = details.get("weapon_damage", 1)
                skill_bonus = details.get("skill_bonus", 0)
                hit, dmg, result = dice_engine.attack_roll(
                    stat, defender_ac, skill_bonus, weapon_dmg
                )
                notes.append(result.detail)
                # Apply damage to NPC if target exists
                if hit and target:
                    npc = self.state.get_npc(target)
                    if npc:
                        npc.current_hp = max(0, npc.current_hp - dmg)
                        if npc.current_hp <= 0:
                            npc.is_alive = False
                            notes.append(f"{npc.name} has been defeated!")

            elif action_type == "npc_dialogue":
                npc_response = self._delegate_to_npc(target, details.get("context", ""))
                if npc_response:
                    notes.append(f"[NPC] {npc_response}")

            elif action_type == "rest":
                healed = self.state.player.heal(details.get("amount", 5))
                notes.append(f"Rested. Healed {healed} HP.")

        return notes

    # ------------------------------------------------------------------
    # NPC delegation
    # ------------------------------------------------------------------

    def _get_npc_agent(self, npc_id: str) -> NPCAgent | None:
        """Lazily create or retrieve an NPC agent."""
        npc = self.state.get_npc(npc_id)
        if not npc:
            return None
        if npc_id not in self._npc_agents:
            self._npc_agents[npc_id] = NPCAgent(llm=self.llm, npc=npc)
        return self._npc_agents[npc_id]

    def _delegate_to_npc(self, npc_id: str, context: str) -> str:
        """Hand off a conversation turn to an NPC agent."""
        agent = self._get_npc_agent(npc_id)
        if not agent:
            return ""

        npc = self.state.get_npc(npc_id)
        response_raw = agent.process(context)

        # Try to parse structured NPC response
        try:
            data = json.loads(response_raw)
            dialogue = data.get("dialogue", response_raw)
            disp_shift = data.get("disposition_shift", 0)
            memory_note = data.get("memory_note", "")

            if disp_shift and npc:
                self.state.adjust_relationship(npc_id, disp_shift)

            if memory_note and npc:
                self.memory_mgr.add_interaction(npc, summary=memory_note)

            return dialogue
        except (json.JSONDecodeError, TypeError):
            return response_raw

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def begin_adventure(self) -> str:
        """Generate the opening narration for the campaign."""
        context = self._build_context()
        prompt = (
            "The adventure begins. Set the scene for the player based on the "
            "campaign setting and their starting location. Make it atmospheric "
            "and inviting. End with a hook or prompt for the player's first action."
        )
        raw = self._chat(prompt, extra_system=context)
        parsed = self._parse_gm_response(raw)
        narrative = parsed.get("narrative", raw)

        self.state.world.add_narrative(narrative)
        self.state.world.gm_history.append({"role": "assistant", "content": narrative})
        return narrative

    def process_action(self, player_input: str) -> str:
        """Process a player's natural-language action and return the narrative."""
        context = self._build_context()

        # Add player input to history
        self.state.world.gm_history.append({"role": "user", "content": player_input})
        self.state.world.trim_gm_history()

        raw = self._chat(
            player_input,
            history=self.state.world.gm_history[:-1],  # exclude the one we just added
            extra_system=context,
        )

        parsed = self._parse_gm_response(raw)
        narrative = parsed.get("narrative", raw)
        actions = parsed.get("actions", [])
        mechanical = parsed.get("mechanical_notes", "")

        # Execute any structured actions
        action_notes = self._process_actions(actions)

        # Combine mechanical info
        if action_notes:
            mechanical_block = " | ".join(action_notes)
            if mechanical:
                mechanical = f"{mechanical} | {mechanical_block}"
            else:
                mechanical = mechanical_block

        # Build final output
        output = narrative
        if mechanical:
            output += f"\n[dim]({mechanical})[/dim]"

        # Update state
        self.state.world.add_narrative(narrative)
        self.state.world.gm_history.append({"role": "assistant", "content": narrative})
        self.state.world.trim_gm_history()

        return output

    def process(self, input_text: str, **kwargs: Any) -> str:
        """BaseAgent interface — routes to process_action."""
        return self.process_action(input_text)
