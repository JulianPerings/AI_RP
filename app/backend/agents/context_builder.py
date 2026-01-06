"""
Session context builder for the Game Master agent.

Builds rich context including player inventory, nearby NPCs, items at location,
and active quests to give the GM comprehensive awareness without tool calls.
"""
import logging
from typing import Optional
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

from models import (
    PlayerCharacter, NonPlayerCharacter, Location, Quest,
    ItemTemplate, ItemInstance, OwnerType, Region
)
from .prompts import RULEBOOK_REFERENCE


def build_session_context(db: Session, player_id: int) -> dict:
    """
    Build comprehensive session context for the Game Master.
    
    Includes:
    - Player basic info (name, class, level, health, gold)
    - Current location details
    - Player inventory (with hint to use get_player_inventory for details)
    - NPCs at current location (with hint to use get_npc_info for details)
    - Items at current location (with hint to use get_items_at_location for details)
    - Active quests (with hint to use get_player_quests for details)
    
    Returns:
        dict with all context data formatted for LLM consumption
    """
    player = db.query(PlayerCharacter).filter(PlayerCharacter.id == player_id).first()
    if not player:
        return {"error": f"Player {player_id} not found"}
    
    context = {
        "player_id": player_id,
        "player_name": player.name,
        "player_class": player.character_class,
        "player_level": player.level,
        "player_health": player.health,
        "player_max_health": player.max_health,
        "player_gold": player.gold,
        "location_id": player.current_location_id,
    }
    
    # Current location and region
    if player.current_location_id:
        location = db.query(Location).filter(Location.id == player.current_location_id).first()
        if location:
            context["location_name"] = location.name
            context["location_description"] = location.description
            context["location_type"] = location.location_type
            context["region_id"] = location.region_id
            
            # Get region info if location has one
            if location.region_id:
                region = db.query(Region).filter(Region.id == location.region_id).first()
                if region:
                    context["region_name"] = region.name
                    context["region_description"] = region.description
                    context["region_races"] = region.dominant_race_description
                    context["region_wealth"] = region.wealth_level.value if region.wealth_level else None
                    context["region_climate"] = region.climate.value if region.climate else None
                    context["region_political"] = region.political_description
                    context["region_danger"] = region.danger_level.value if region.danger_level else None
                    context["region_threats"] = region.threats_description
    
    # Player inventory summary
    inventory_items = db.query(ItemInstance).filter(
        ItemInstance.owner_type == OwnerType.PC,
        ItemInstance.owner_id == player_id
    ).all()
    
    inventory_summary = []
    for item in inventory_items:
        template = db.query(ItemTemplate).filter(ItemTemplate.id == item.template_id).first()
        item_name = item.custom_name or (template.name if template else "Unknown")
        equipped_str = " [EQUIPPED]" if item.is_equipped else ""
        inventory_summary.append(f"{item_name} (x{item.quantity}){equipped_str}")
    
    context["inventory"] = inventory_summary
    context["inventory_count"] = len(inventory_summary)
    
    # NPCs at current location
    if player.current_location_id:
        npcs = db.query(NonPlayerCharacter).filter(
            NonPlayerCharacter.location_id == player.current_location_id
        ).all()
        
        npc_summary = []
        for npc in npcs:
            behavior = npc.behavior_state.value if npc.behavior_state else "passive"
            npc_summary.append({
                "id": npc.id,
                "name": npc.name,
                "type": npc.npc_type,
                "behavior": behavior,
                "health": f"{npc.health}/{npc.max_health}"
            })
        
        context["npcs_here"] = npc_summary
        context["npcs_count"] = len(npc_summary)
    
    # Items at current location (on ground)
    if player.current_location_id:
        ground_items = db.query(ItemInstance).filter(
            ItemInstance.location_id == player.current_location_id,
            ItemInstance.owner_type == OwnerType.NONE
        ).all()
        
        items_summary = []
        for item in ground_items:
            template = db.query(ItemTemplate).filter(ItemTemplate.id == item.template_id).first()
            item_name = item.custom_name or (template.name if template else "Unknown")
            items_summary.append({
                "instance_id": item.id,
                "name": item_name,
                "quantity": item.quantity
            })
        
        context["items_here"] = items_summary
        context["items_here_count"] = len(items_summary)
    
    # Companions following this player
    companions = db.query(NonPlayerCharacter).filter(
        NonPlayerCharacter.following_player_id == player_id
    ).all()
    
    companion_summary = []
    for npc in companions:
        companion_summary.append({
            "id": npc.id,
            "name": npc.name,
            "type": npc.npc_type,
            "health": f"{npc.health}/{npc.max_health}"
        })
    
    context["companions"] = companion_summary
    context["companion_count"] = len(companion_summary)
    
    # Active quests
    quests = db.query(Quest).filter(
        Quest.player_id == player_id,
        Quest.is_active == True
    ).all()
    
    quest_summary = []
    for quest in quests:
        quest_summary.append({
            "id": quest.id,
            "title": quest.title,
            "completed": quest.is_completed
        })
    
    context["active_quests"] = quest_summary
    context["quest_count"] = len(quest_summary)
    
    return context


def format_context_for_prompt(context: dict) -> str:
    """
    Format the session context dict into a string for the system prompt.
    
    Includes hints to use tool calls for detailed information.
    """
    if "error" in context:
        return f"Error loading context: {context['error']}"
    
    lines = []
    
    # Player info
    lines.append(f"## Current Session")
    lines.append(f"- **Player**: {context.get('player_name', 'Unknown')} (ID: {context.get('player_id')})")
    lines.append(f"- **Class**: {context.get('player_class', 'Unknown')} | **Level**: {context.get('player_level', 1)}")
    lines.append(f"- **Health**: {context.get('player_health', 0)}/{context.get('player_max_health', 100)}")
    lines.append(f"- **Gold**: {context.get('player_gold', 0)}")
    
    # Region (if available)
    if context.get("region_name"):
        lines.append(f"\n## Current Region: {context['region_name']}")
        lines.append(f"*{context.get('region_description', '')}*")
        lines.append(f"- **Dominant Races**: {context.get('region_races', 'Various')}")
        lines.append(f"- **Wealth**: {context.get('region_wealth', 'modest')} | **Danger**: {context.get('region_danger', 'low')} | **Climate**: {context.get('region_climate', 'temperate')}")
        if context.get("region_political"):
            lines.append(f"- **Political**: {context['region_political']}")
        if context.get("region_threats"):
            lines.append(f"- **Known Threats**: {context['region_threats']}")
    
    # Location
    if context.get("location_name"):
        lines.append(f"\n## Current Location: {context['location_name']} ({context.get('location_type', 'unknown')})")
        if context.get("location_description"):
            lines.append(f"{context['location_description']}")
    
    # Inventory
    lines.append(f"\n## Inventory ({context.get('inventory_count', 0)} items)")
    if context.get("inventory"):
        for item in context["inventory"][:10]:  # Show first 10
            lines.append(f"- {item}")
        if context.get("inventory_count", 0) > 10:
            lines.append(f"- ...and {context['inventory_count'] - 10} more (use get_player_inventory for full list)")
    else:
        lines.append("- Empty")
    lines.append("*(Use get_player_inventory for instance_ids needed for transfers)*")
    
    # Companions
    lines.append(f"\n## Companions ({context.get('companion_count', 0)})")
    if context.get("companions"):
        for comp in context["companions"]:
            lines.append(f"- **{comp['name']}** (ID:{comp['id']}) - {comp['type']}, HP:{comp['health']}")
        lines.append("*(Use dismiss_companion(npc_id) if player tells them to stay/wait)*")
    else:
        lines.append("- None following")
    
    # NPCs here (excluding companions, they're listed above)
    lines.append(f"\n## Other NPCs Here ({context.get('npcs_count', 0)})")
    if context.get("npcs_here"):
        companion_ids = {c['id'] for c in context.get("companions", [])}
        other_npcs = [npc for npc in context["npcs_here"] if npc['id'] not in companion_ids]
        for npc in other_npcs:
            lines.append(f"- **{npc['name']}** (ID:{npc['id']}) - {npc['type']}, {npc['behavior']}, HP:{npc['health']}")
        if not other_npcs:
            lines.append("- None")
    else:
        lines.append("- None")
    lines.append("*(Use get_npc_info(id) for personality, relationships, dialogue)*")
    
    # Items on ground
    lines.append(f"\n## Items on Ground ({context.get('items_here_count', 0)})")
    if context.get("items_here"):
        for item in context["items_here"]:
            lines.append(f"- {item['name']} x{item['quantity']} (instance_id:{item['instance_id']})")
    else:
        lines.append("- None")
    lines.append("*(Use pickup_item(player_id, instance_id) to pick up)*")
    
    # Quests
    lines.append(f"\n## Active Quests ({context.get('quest_count', 0)})")
    if context.get("active_quests"):
        for quest in context["active_quests"]:
            status = "✓" if quest['completed'] else "○"
            lines.append(f"- [{status}] {quest['title']} (ID:{quest['id']})")
    else:
        lines.append("- None")
    lines.append("*(Use get_player_quests for full quest details)*")
    
    # Rulebook reference for world-building
    lines.append(f"\n---\n# World Building Rulebook\n{RULEBOOK_REFERENCE}")
    
    return "\n".join(lines)
