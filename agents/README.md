# Agents

LLM-powered agents that drive the AI RPG. Each agent loads its system prompt from a markdown file in `prompts/` and communicates via the `LLMService`.

## Files

| File                   | Description                                                   |
|------------------------|---------------------------------------------------------------|
| `base_agent.py`        | Abstract base class — prompt loading, LLM helpers             |
| `gamemaster.py`        | Orchestrator — narrates, delegates, processes structured actions |
| `npc_agent.py`         | Per-NPC agent — dialogue and behaviour, stays in character    |
| `campaign_creator.py`  | Generates campaign YAML files from high-level descriptions    |

## Prompts

System prompts live in `prompts/` as markdown files:

| File                    | Used By              |
|-------------------------|----------------------|
| `gamemaster.md`         | GameMasterAgent      |
| `npc.md`                | NPCAgent             |
| `campaign_creator.md`   | CampaignCreatorAgent |

Edit these to tweak agent behaviour without touching code.

## Architecture

```
Player Input → GameMasterAgent
                ├── narrates outcome
                ├── emits structured actions (JSON)
                │     → state_manager applies changes
                │     → dice engine resolves checks/combat
                └── delegates NPC dialogue → NPCAgent
                      → memory_manager records interaction
```
