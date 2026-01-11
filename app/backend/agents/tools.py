from typing import Optional, List
from langchain_core.tools import tool
from sqlalchemy.orm import Session

from datetime import datetime
from database import SessionLocal
from models import (
    PlayerCharacter, NonPlayerCharacter, Location, Quest,
    ItemTemplate, ItemInstance, Race, Faction,
    CharacterRelationship, CharacterType, OwnerType,
    Region, ClimateType, WealthLevel, DangerLevel,
    RaceRelationship, CombatSession
)
from agents.story_manager import get_story_manager


def get_db():
    """Get database session for tools."""
    db = SessionLocal()
    try:
        return db
    finally:
        pass


@tool
def get_player_info(player_id: int) -> dict:
    """Get detailed information about a player character including their stats, inventory, and current location."""
    db = SessionLocal()
    try:
        player = db.query(PlayerCharacter).filter(PlayerCharacter.id == player_id).first()
        if not player:
            return {"error": f"Player with id {player_id} not found"}
        
        location = None
        if player.current_location_id:
            loc = db.query(Location).filter(Location.id == player.current_location_id).first()
            if loc:
                location = {"id": loc.id, "name": loc.name, "description": loc.description}
        
        race = None
        if player.race_id:
            r = db.query(Race).filter(Race.id == player.race_id).first()
            if r:
                race = {"id": r.id, "name": r.name}
        
        faction = None
        if player.primary_faction_id:
            f = db.query(Faction).filter(Faction.id == player.primary_faction_id).first()
            if f:
                faction = {"id": f.id, "name": f.name}
        
        items = db.query(ItemInstance).filter(
            ItemInstance.owner_type == OwnerType.PC,
            ItemInstance.owner_id == player_id
        ).all()
        
        inventory = []
        for item in items:
            template = db.query(ItemTemplate).filter(ItemTemplate.id == item.template_id).first()
            if template:
                inventory.append({
                    "instance_id": item.id,
                    "name": item.custom_name or template.name,
                    "category": template.category.value,
                    "equipped": item.is_equipped,
                    "quantity": item.quantity
                })
        
        return {
            "id": player.id,
            "name": player.name,
            "class": player.character_class,
            "level": player.level,
            "health": player.health,
            "max_health": player.max_health,
            "experience": player.experience,
            "gold": player.gold,
            "description": player.description,
            "race": race,
            "faction": faction,
            "location": location,
            "inventory": inventory,
            "reputation": player.reputation or {}
        }
    finally:
        db.close()


@tool
def get_location_info(location_id: int) -> dict:
    """Get information about a location including NPCs and items present there."""
    db = SessionLocal()
    try:
        location = db.query(Location).filter(Location.id == location_id).first()
        if not location:
            return {"error": f"Location with id {location_id} not found"}
        
        npcs = db.query(NonPlayerCharacter).filter(
            NonPlayerCharacter.location_id == location_id
        ).all()
        
        npc_list = [{
            "id": npc.id,
            "name": npc.name,
            "type": npc.npc_type,
            "behavior": npc.behavior_state.value if npc.behavior_state else "passive"
        } for npc in npcs]
        
        items = db.query(ItemInstance).filter(
            ItemInstance.location_id == location_id,
            ItemInstance.owner_type == OwnerType.NONE
        ).all()
        
        item_list = []
        for item in items:
            template = db.query(ItemTemplate).filter(ItemTemplate.id == item.template_id).first()
            if template:
                item_list.append({
                    "instance_id": item.id,
                    "name": item.custom_name or template.name,
                    "category": template.category.value
                })
        
        return {
            "id": location.id,
            "name": location.name,
            "description": location.description,
            "type": location.location_type,
            "npcs": npc_list,
            "items_on_ground": item_list
        }
    finally:
        db.close()


@tool
def get_npc_info(npc_id: int) -> dict:
    """Get detailed information about an NPC including their personality and relationship with players."""
    db = SessionLocal()
    try:
        npc = db.query(NonPlayerCharacter).filter(NonPlayerCharacter.id == npc_id).first()
        if not npc:
            return {"error": f"NPC with id {npc_id} not found"}
        
        race = None
        if npc.race_id:
            r = db.query(Race).filter(Race.id == npc.race_id).first()
            if r:
                race = {"id": r.id, "name": r.name}
        
        faction = None
        if npc.faction_id:
            f = db.query(Faction).filter(Faction.id == npc.faction_id).first()
            if f:
                faction = {"id": f.id, "name": f.name, "alignment": f.alignment.value if f.alignment else "neutral"}
        
        location = None
        if npc.location_id:
            loc = db.query(Location).filter(Location.id == npc.location_id).first()
            if loc:
                location = {"id": loc.id, "name": loc.name}
        
        return {
            "id": npc.id,
            "name": npc.name,
            "type": npc.npc_type,
            "health": npc.health,
            "max_health": npc.max_health,
            "behavior_state": npc.behavior_state.value if npc.behavior_state else "passive",
            "base_disposition": npc.base_disposition,
            "description": npc.description,
            "dialogue": npc.dialogue,
            "race": race,
            "faction": faction,
            "location": location,
            "personality_traits": npc.personality_traits or {}
        }
    finally:
        db.close()


@tool
def get_relationship(source_type: str, source_id: int, target_type: str, target_id: int) -> dict:
    """Get the personal relationship between two characters (PC↔NPC or NPC↔NPC).
    
    NOT for racial relationships - use get_race_relationships() for that.
    Types: 'PC' or 'NPC'
    """
    db = SessionLocal()
    try:
        src_type = CharacterType.PC if source_type.upper() == "PC" else CharacterType.NPC
        tgt_type = CharacterType.PC if target_type.upper() == "PC" else CharacterType.NPC
        
        # Normalize direction: PC always first, or lower ID first if same type
        if src_type == CharacterType.NPC and tgt_type == CharacterType.PC:
            src_type, tgt_type = tgt_type, src_type
            source_id, target_id = target_id, source_id
        elif src_type == tgt_type and source_id > target_id:
            source_id, target_id = target_id, source_id
        
        rel = db.query(CharacterRelationship).filter(
            CharacterRelationship.source_character_type == src_type,
            CharacterRelationship.source_character_id == source_id,
            CharacterRelationship.target_character_type == tgt_type,
            CharacterRelationship.target_character_id == target_id
        ).first()
        
        if not rel:
            return {
                "exists": False,
                "relationship_value": 0,
                "relationship_type": "neutral",
                "notes": "No established relationship"
            }
        
        return {
            "exists": True,
            "id": rel.id,
            "relationship_value": rel.relationship_value,
            "relationship_type": rel.relationship_type.value if rel.relationship_type else "neutral",
            "notes": rel.notes,
            "last_interaction": str(rel.last_interaction) if rel.last_interaction else None
        }
    finally:
        db.close()


@tool
def update_relationship(source_type: str, source_id: int, target_type: str, target_id: int, 
                        value_change: int, notes: Optional[str] = None) -> dict:
    """Update personal relationship between two characters (PC↔NPC or NPC↔NPC).
    
    NOT for racial relationships - use update_race_relationship() for that.
    value_change is added to current (-100 to +100 range). Types: 'PC' or 'NPC'
    """
    db = SessionLocal()
    try:
        src_type = CharacterType.PC if source_type.upper() == "PC" else CharacterType.NPC
        tgt_type = CharacterType.PC if target_type.upper() == "PC" else CharacterType.NPC
        
        # Normalize direction: PC always first, or lower ID first if same type
        if src_type == CharacterType.NPC and tgt_type == CharacterType.PC:
            # Swap: PC should be source
            src_type, tgt_type = tgt_type, src_type
            source_id, target_id = target_id, source_id
        elif src_type == tgt_type and source_id > target_id:
            # Swap: lower ID first
            source_id, target_id = target_id, source_id
        
        # Check for existing relationship in canonical direction
        rel = db.query(CharacterRelationship).filter(
            CharacterRelationship.source_character_type == src_type,
            CharacterRelationship.source_character_id == source_id,
            CharacterRelationship.target_character_type == tgt_type,
            CharacterRelationship.target_character_id == target_id
        ).first()
        
        if rel:
            new_value = max(-100, min(100, rel.relationship_value + value_change))
            rel.relationship_value = new_value
            if notes:
                rel.notes = notes
            db.commit()
            return {"updated": True, "new_value": new_value}
        else:
            new_value = max(-100, min(100, value_change))
            new_rel = CharacterRelationship(
                source_character_type=src_type,
                source_character_id=source_id,
                target_character_type=tgt_type,
                target_character_id=target_id,
                relationship_value=new_value,
                notes=notes
            )
            db.add(new_rel)
            db.commit()
            return {"created": True, "new_value": new_value}
    finally:
        db.close()


@tool
def get_player_quests(player_id: int) -> List[dict]:
    """Get all quests associated with a player character."""
    db = SessionLocal()
    try:
        quests = db.query(Quest).filter(Quest.player_id == player_id).all()
        return [{
            "id": q.id,
            "title": q.title,
            "description": q.description,
            "is_active": q.is_active,
            "is_completed": q.is_completed,
            "reward_gold": q.reward_gold,
            "reward_experience": q.reward_experience
        } for q in quests]
    finally:
        db.close()


@tool
def create_quest(player_id: int, title: str, description: str, 
                  reward_gold: int = 0, reward_experience: int = 0) -> dict:
    """Create a new quest for a player."""
    db = SessionLocal()
    try:
        quest = Quest(
            title=title,
            description=description,
            is_active=True,
            is_completed=False,
            reward_gold=reward_gold,
            reward_experience=reward_experience,
            player_id=player_id
        )
        db.add(quest)
        db.commit()
        db.refresh(quest)
        return {"created": True, "quest_id": quest.id, "title": title}
    finally:
        db.close()


@tool
def update_quest_status(quest_id: int, is_active: bool = None, is_completed: bool = None) -> dict:
    """Update the status of a quest. Set is_completed=True when quest is done, is_active=False to abandon."""
    db = SessionLocal()
    try:
        quest = db.query(Quest).filter(Quest.id == quest_id).first()
        if not quest:
            return {"error": f"Quest with id {quest_id} not found"}
        
        if is_active is not None:
            quest.is_active = is_active
        if is_completed is not None:
            quest.is_completed = is_completed
            if is_completed:
                quest.is_active = False
        db.commit()
        return {"updated": True, "quest_id": quest_id, "is_active": quest.is_active, "is_completed": quest.is_completed}
    finally:
        db.close()


@tool
def create_item_for_player(player_id: int, template_id: int, quantity: int = 1, custom_name: Optional[str] = None,
                          buffs: Optional[List[str]] = None, flaws: Optional[List[str]] = None,
                          enchantments: Optional[List[str]] = None) -> dict:
    """CREATE a NEW item instance from a template and give it to a player.
    
    WARNING: This creates items out of thin air. Use only for rewards, loot drops, or quest items.
    To transfer an EXISTING item, use transfer_item with the item's instance_id instead.
    
    Make items unique with:
    - buffs: ["sharp: +2 damage", "lightweight"]
    - flaws: ["rusty: -1 durability", "chipped"]
    - enchantments: ["fire: +5 fire damage", "glowing: emits light"]
    """
    db = SessionLocal()
    try:
        template = db.query(ItemTemplate).filter(ItemTemplate.id == template_id).first()
        if not template:
            return {"error": f"Item template with id {template_id} not found"}
        
        player = db.query(PlayerCharacter).filter(PlayerCharacter.id == player_id).first()
        if not player:
            return {"error": f"Player with id {player_id} not found"}
        
        item = ItemInstance(
            template_id=template_id,
            owner_type=OwnerType.PC,
            owner_id=player_id,
            quantity=quantity,
            custom_name=custom_name,
            buffs=buffs or [],
            flaws=flaws or [],
            enchantments=enchantments or []
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        
        return {
            "given": True,
            "instance_id": item.id,
            "item_name": custom_name or template.name,
            "quantity": quantity,
            "to_player": player.name,
            "buffs": item.buffs,
            "flaws": item.flaws,
            "enchantments": item.enchantments
        }
    finally:
        db.close()


@tool
def update_player_gold(player_id: int, gold_change: int) -> dict:
    """Add or remove gold from a player. Use negative values to remove gold."""
    db = SessionLocal()
    try:
        player = db.query(PlayerCharacter).filter(PlayerCharacter.id == player_id).first()
        if not player:
            return {"error": f"Player with id {player_id} not found"}
        
        new_gold = max(0, player.gold + gold_change)
        player.gold = new_gold
        db.commit()
        
        return {"updated": True, "new_gold": new_gold, "change": gold_change}
    finally:
        db.close()


@tool
def update_player_health(player_id: int, health_change: int) -> dict:
    """Add or remove health from a player. Use negative values for damage."""
    db = SessionLocal()
    try:
        player = db.query(PlayerCharacter).filter(PlayerCharacter.id == player_id).first()
        if not player:
            return {"error": f"Player with id {player_id} not found"}
        
        new_health = max(0, min(player.max_health, player.health + health_change))
        player.health = new_health

        combat = db.query(CombatSession).filter(
            CombatSession.player_id == player_id,
            CombatSession.status == "active"
        ).first()
        if combat:
            updated = False
            team_player = list(combat.team_player or [])
            for m in team_player:
                if m.get("type") == "PC" and m.get("id") == player_id:
                    m["hp"] = new_health
                    m["max_hp"] = player.max_health
                    updated = True
                    break
            if updated:
                combat.team_player = team_player

        db.commit()
        
        return {
            "updated": True,
            "new_health": new_health,
            "max_health": player.max_health,
            "change": health_change,
            "is_dead": new_health <= 0
        }
    finally:
        db.close()


@tool
def move_player(player_id: int, location_id: int) -> dict:
    """Move a player to a new location. Companions following the player will automatically move with them."""
    db = SessionLocal()
    try:
        player = db.query(PlayerCharacter).filter(PlayerCharacter.id == player_id).first()
        if not player:
            return {"error": f"Player with id {player_id} not found"}
        
        location = db.query(Location).filter(Location.id == location_id).first()
        if not location:
            return {"error": f"Location with id {location_id} not found"}
        
        old_location_id = player.current_location_id
        player.current_location_id = location_id
        
        # Auto-move companions who are following this player
        companions = db.query(NonPlayerCharacter).filter(
            NonPlayerCharacter.following_player_id == player_id
        ).all()
        
        companions_moved = []
        for companion in companions:
            companion.location_id = location_id
            companions_moved.append(companion.name)
        
        db.commit()
        
        result = {
            "moved": True,
            "player": player.name,
            "from_location_id": old_location_id,
            "to_location": {"id": location.id, "name": location.name, "description": location.description}
        }
        
        if companions_moved:
            result["companions_moved"] = companions_moved
        
        return result
    finally:
        db.close()


@tool
def list_item_templates(category: Optional[str] = None, search: Optional[str] = None) -> List[dict]:
    """List available item templates, optionally filtered by category or name search.
    
    IMPORTANT: Always search for existing templates before creating new ones!
    Use search parameter to find templates by name (case-insensitive partial match).
    
    Args:
        category: Filter by category (weapon, armor, potion, food, quest, material, misc)
        search: Search term for template name (e.g., "sword", "potion", "bread")
    
    Example: list_item_templates(search="sword") to find sword templates
    """
    db = SessionLocal()
    try:
        query = db.query(ItemTemplate)
        if category:
            query = query.filter(ItemTemplate.category == category)
        if search:
            query = query.filter(ItemTemplate.name.ilike(f"%{search}%"))
        
        templates = query.all()
        return [{
            "id": t.id,
            "name": t.name,
            "category": t.category.value,
            "rarity": t.rarity.value if t.rarity else "common",
            "description": t.description,
            "properties": t.properties
        } for t in templates]
    finally:
        db.close()


@tool
def move_npc(npc_id: int, location_id: int) -> dict:
    """Move an NPC to a new location."""
    db = SessionLocal()
    try:
        npc = db.query(NonPlayerCharacter).filter(NonPlayerCharacter.id == npc_id).first()
        if not npc:
            return {"error": f"NPC with id {npc_id} not found"}
        
        location = db.query(Location).filter(Location.id == location_id).first()
        if not location:
            return {"error": f"Location with id {location_id} not found"}
        
        old_location_id = npc.location_id
        npc.location_id = location_id
        db.commit()
        
        return {
            "moved": True,
            "npc": npc.name,
            "from_location_id": old_location_id,
            "to_location": {"id": location.id, "name": location.name}
        }
    finally:
        db.close()


@tool
def update_npc_health(npc_id: int, health_change: int) -> dict:
    """Add or remove health from an NPC. Use negative values for damage."""
    db = SessionLocal()
    try:
        npc = db.query(NonPlayerCharacter).filter(NonPlayerCharacter.id == npc_id).first()
        if not npc:
            return {"error": f"NPC with id {npc_id} not found"}
        
        new_health = max(0, min(npc.max_health, npc.health + health_change))
        npc.health = new_health

        # Keep any active combat trackers in sync (NPCs can be allies or enemies)
        combats = db.query(CombatSession).filter(CombatSession.status == "active").all()
        for combat in combats:
            updated = False

            team_player = list(combat.team_player or [])
            for m in team_player:
                if m.get("type") == "NPC" and m.get("id") == npc_id:
                    m["hp"] = new_health
                    m["max_hp"] = npc.max_health
                    updated = True
                    break
            if updated:
                combat.team_player = team_player

            team_enemy = list(combat.team_enemy or [])
            for m in team_enemy:
                if m.get("type") == "NPC" and m.get("id") == npc_id:
                    m["hp"] = new_health
                    m["max_hp"] = npc.max_health
                    updated = True
                    break
            if updated:
                combat.team_enemy = team_enemy
        
        db.commit()
        
        return {
            "updated": True,
            "npc": npc.name,
            "new_health": new_health,
            "max_health": npc.max_health,
            "change": health_change,
            "is_dead": new_health <= 0
        }
    finally:
        db.close()


@tool
def update_npc_behavior(npc_id: int, behavior_state: str) -> dict:
    """Update an NPC's behavior state. Valid states: passive, defensive, aggressive, hostile, protective."""
    from models import BehaviorState
    db = SessionLocal()
    try:
        npc = db.query(NonPlayerCharacter).filter(NonPlayerCharacter.id == npc_id).first()
        if not npc:
            return {"error": f"NPC with id {npc_id} not found"}
        
        try:
            new_state = BehaviorState(behavior_state.lower())
        except ValueError:
            return {"error": f"Invalid behavior state: {behavior_state}. Valid: passive, defensive, aggressive, hostile, protective"}
        
        old_state = npc.behavior_state.value if npc.behavior_state else "passive"
        npc.behavior_state = new_state
        db.commit()
        
        return {
            "updated": True,
            "npc": npc.name,
            "old_behavior": old_state,
            "new_behavior": new_state.value
        }
    finally:
        db.close()


@tool
def update_npc_disposition(npc_id: int, disposition_change: int) -> dict:
    """Update an NPC's base disposition toward players. Range: -100 to 100."""
    db = SessionLocal()
    try:
        npc = db.query(NonPlayerCharacter).filter(NonPlayerCharacter.id == npc_id).first()
        if not npc:
            return {"error": f"NPC with id {npc_id} not found"}
        
        new_disposition = max(-100, min(100, (npc.base_disposition or 0) + disposition_change))
        npc.base_disposition = new_disposition
        db.commit()
        
        return {
            "updated": True,
            "npc": npc.name,
            "new_disposition": new_disposition,
            "change": disposition_change
        }
    finally:
        db.close()


@tool
def create_npc(name: str, npc_type: str, location_id: int, 
               description: Optional[str] = None, dialogue: Optional[str] = None,
               behavior_state: str = "passive", base_disposition: int = 0,
               race_id: Optional[int] = None, faction_id: Optional[int] = None) -> dict:
    """Create a new NPC. Use list_races() first to get race_id if needed.
    
    Args:
        npc_type: merchant, guard, innkeeper, noble, commoner, etc.
        behavior_state: passive, defensive, aggressive, hostile, protective
        base_disposition: -100 (hostile) to +100 (friendly), default 0 (neutral)
        race_id: Use list_races() to find. Affects racial relationship modifiers.
    """
    from models import BehaviorState
    db = SessionLocal()
    try:
        location = db.query(Location).filter(Location.id == location_id).first()
        if not location:
            return {"error": f"Location with id {location_id} not found"}
        
        try:
            behavior = BehaviorState(behavior_state.lower())
        except ValueError:
            behavior = BehaviorState.PASSIVE
        
        npc = NonPlayerCharacter(
            name=name,
            npc_type=npc_type,
            location_id=location_id,
            description=description,
            dialogue=dialogue,
            behavior_state=behavior,
            base_disposition=base_disposition,
            race_id=race_id,
            faction_id=faction_id,
            health=50,
            max_health=50
        )
        db.add(npc)
        db.commit()
        db.refresh(npc)
        
        return {
            "created": True,
            "npc_id": npc.id,
            "name": name,
            "location": location.name
        }
    finally:
        db.close()


@tool
def list_locations(search: Optional[str] = None, region_id: Optional[int] = None) -> list:
    """List all locations, optionally filtered by search term or region. 
    ALWAYS check this before creating a new location to avoid duplicates!"""
    db = SessionLocal()
    try:
        query = db.query(Location)
        if region_id:
            query = query.filter(Location.region_id == region_id)
        locations = query.all()
        
        results = []
        for loc in locations:
            # Filter by search term if provided
            if search:
                search_lower = search.lower()
                if search_lower not in loc.name.lower() and (not loc.description or search_lower not in loc.description.lower()):
                    continue
            results.append({
                "id": loc.id,
                "name": loc.name,
                "type": loc.location_type,
                "region_id": loc.region_id
            })
        return results
    finally:
        db.close()


@tool
def create_location(name: str, description: str, location_type: Optional[str] = None,
                    region_id: Optional[int] = None, danger_modifier: Optional[int] = None,
                    wealth_modifier: Optional[int] = None, accessibility: Optional[str] = None) -> dict:
    """Create a new location. FIRST use list_locations to check if it already exists!
    
    Args:
        region_id: Link to a region for consistent world-building
        danger_modifier: Adjust region danger (-2 to +2)
        accessibility: public, restricted, hidden, secret
    """
    db = SessionLocal()
    try:
        location = Location(
            name=name,
            description=description,
            location_type=location_type,
            region_id=region_id,
            danger_modifier=danger_modifier,
            wealth_modifier=wealth_modifier,
            accessibility=accessibility
        )
        db.add(location)
        db.commit()
        db.refresh(location)
        
        return {
            "created": True,
            "location_id": location.id,
            "name": name,
            "region_id": region_id
        }
    finally:
        db.close()


@tool  
def create_item_template(name: str, category: str, description: str,
                         rarity: str = "common", weight: int = 1,
                         properties: Optional[dict] = None) -> dict:
    """Create a new item template/blueprint. Categories: weapon, armor, potion, food, quest, material, misc."""
    from models import ItemCategory, ItemRarity
    db = SessionLocal()
    try:
        try:
            cat = ItemCategory(category.lower())
        except ValueError:
            return {"error": f"Invalid category: {category}. Valid: weapon, armor, potion, food, quest, material, misc"}
        
        try:
            rar = ItemRarity(rarity.lower())
        except ValueError:
            rar = ItemRarity.COMMON
        
        template = ItemTemplate(
            name=name,
            category=cat,
            description=description,
            rarity=rar,
            weight=weight,
            properties=properties or {}
        )
        db.add(template)
        db.commit()
        db.refresh(template)
        
        return {
            "created": True,
            "template_id": template.id,
            "name": name,
            "category": category,
            "rarity": rarity
        }
    finally:
        db.close()


@tool
def spawn_item_at_location(template_id: int, location_id: int, 
                           quantity: int = 1, custom_name: Optional[str] = None,
                           buffs: Optional[List[str]] = None, flaws: Optional[List[str]] = None,
                           enchantments: Optional[List[str]] = None) -> dict:
    """Spawn an item on the ground at a location.
    
    Make items unique with:
    - buffs: ["sharp: +2 damage", "lightweight"]
    - flaws: ["rusty: -1 durability", "heavy"]
    - enchantments: ["fire: +5 fire damage", "glowing"]
    """
    db = SessionLocal()
    try:
        template = db.query(ItemTemplate).filter(ItemTemplate.id == template_id).first()
        if not template:
            return {"error": f"Item template with id {template_id} not found"}
        
        location = db.query(Location).filter(Location.id == location_id).first()
        if not location:
            return {"error": f"Location with id {location_id} not found"}
        
        item = ItemInstance(
            template_id=template_id,
            owner_type=OwnerType.NONE,
            owner_id=None,
            location_id=location_id,
            quantity=quantity,
            custom_name=custom_name,
            buffs=buffs or [],
            flaws=flaws or [],
            enchantments=enchantments or []
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        
        return {
            "spawned": True,
            "instance_id": item.id,
            "item_name": custom_name or template.name,
            "location": location.name,
            "enchantments": item.enchantments
        }
    finally:
        db.close()


@tool
def create_item_for_npc(npc_id: int, template_id: int, 
                        quantity: int = 1, custom_name: Optional[str] = None,
                        buffs: Optional[List[str]] = None, flaws: Optional[List[str]] = None,
                        enchantments: Optional[List[str]] = None) -> dict:
    """CREATE a NEW item instance from a template and give it to an NPC.
    
    WARNING: This creates items out of thin air. Use only for NPC inventory setup.
    To transfer an EXISTING item, use transfer_item with the item's instance_id instead.
    
    Make items unique with:
    - buffs: ["masterwork: +3 damage", "blessed"]
    - flaws: ["cursed: drains health", "fragile"]
    - enchantments: ["frost: +5 cold damage", "vampiric: heals on hit"]
    """
    db = SessionLocal()
    try:
        template = db.query(ItemTemplate).filter(ItemTemplate.id == template_id).first()
        if not template:
            return {"error": f"Item template with id {template_id} not found"}
        
        npc = db.query(NonPlayerCharacter).filter(NonPlayerCharacter.id == npc_id).first()
        if not npc:
            return {"error": f"NPC with id {npc_id} not found"}
        
        item = ItemInstance(
            template_id=template_id,
            owner_type=OwnerType.NPC,
            owner_id=npc_id,
            quantity=quantity,
            custom_name=custom_name,
            buffs=buffs or [],
            flaws=flaws or [],
            enchantments=enchantments or []
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        
        return {
            "given": True,
            "instance_id": item.id,
            "item_name": custom_name or template.name,
            "to_npc": npc.name,
            "enchantments": item.enchantments
        }
    finally:
        db.close()


@tool
def transfer_item(item_instance_id: int, new_owner_type: str, 
                  new_owner_id: Optional[int] = None, location_id: Optional[int] = None) -> dict:
    """Transfer an EXISTING item instance between owners.
    
    Use this to move items that already exist in the world (picked up, traded, dropped).
    - Get item instance_id from: get_items_at_location, get_player_inventory, or get_npc_inventory
    - new_owner_type: 'PC' (player), 'NPC', or 'NONE' (drop on ground)
    - For NONE (drop), provide location_id where item should be placed
    """
    db = SessionLocal()
    try:
        item = db.query(ItemInstance).filter(ItemInstance.id == item_instance_id).first()
        if not item:
            return {"error": f"Item instance with id {item_instance_id} not found"}
        
        template = db.query(ItemTemplate).filter(ItemTemplate.id == item.template_id).first()
        item_name = item.custom_name or (template.name if template else "Unknown item")
        
        try:
            owner_type = OwnerType(new_owner_type.upper())
        except ValueError:
            return {"error": f"Invalid owner type: {new_owner_type}. Valid: PC, NPC, NONE"}
        
        old_owner = f"{item.owner_type.value}:{item.owner_id}" if item.owner_type else "ground"
        
        item.owner_type = owner_type
        item.owner_id = new_owner_id if owner_type != OwnerType.NONE else None
        item.location_id = location_id if owner_type == OwnerType.NONE else None
        item.is_equipped = False
        db.commit()
        
        return {
            "transferred": True,
            "item": item_name,
            "from": old_owner,
            "to": f"{owner_type.value}:{new_owner_id}" if new_owner_id else "ground"
        }
    finally:
        db.close()


@tool
def consume_item_instance(item_instance_id: int, amount: int = 1) -> dict:
    """Consume an item stack by decreasing its quantity.

    Use this for ammo and consumables (arrows, potions, bandages, rations, etc.).
    This mutates the existing ItemInstance quantity and deletes the instance when it reaches 0.

    IMPORTANT:
    - You need an `instance_id` from get_player_inventory / get_npc_inventory / get_items_at_location.
    - This is for consumption, not transfer. Use transfer_item to move ownership.
    """
    db = SessionLocal()
    try:
        if item_instance_id <= 0:
            return {"error": "item_instance_id must be a positive integer"}
        if amount <= 0:
            return {"error": "amount must be a positive integer"}

        item = db.query(ItemInstance).filter(ItemInstance.id == item_instance_id).first()
        if not item:
            return {"error": f"Item instance with id {item_instance_id} not found"}

        template = db.query(ItemTemplate).filter(ItemTemplate.id == item.template_id).first()
        item_name = item.custom_name or (template.name if template else "Unknown")

        if item.quantity is None:
            item.quantity = 1

        consumed = min(int(amount), int(item.quantity))
        item.quantity = int(item.quantity) - consumed

        deleted = False
        if item.quantity <= 0:
            db.delete(item)
            deleted = True

        db.commit()

        return {
            "consumed": True,
            "item": item_name,
            "instance_id": item_instance_id,
            "amount": consumed,
            "quantity_remaining": 0 if deleted else item.quantity,
            "deleted": deleted
        }
    finally:
        db.close()


@tool
def get_npcs_at_location(location_id: int) -> List[dict]:
    """Get all NPCs at a specific location."""
    db = SessionLocal()
    try:
        npcs = db.query(NonPlayerCharacter).filter(
            NonPlayerCharacter.location_id == location_id
        ).all()
        
        return [{
            "id": npc.id,
            "name": npc.name,
            "type": npc.npc_type,
            "health": npc.health,
            "max_health": npc.max_health,
            "behavior": npc.behavior_state.value if npc.behavior_state else "passive",
            "disposition": npc.base_disposition
        } for npc in npcs]
    finally:
        db.close()


@tool
def update_player_experience(player_id: int, exp_change: int) -> dict:
    """Add experience to a player. Automatically handles level ups (100 exp per level)."""
    db = SessionLocal()
    try:
        player = db.query(PlayerCharacter).filter(PlayerCharacter.id == player_id).first()
        if not player:
            return {"error": f"Player with id {player_id} not found"}
        
        old_level = player.level
        player.experience = (player.experience or 0) + exp_change
        
        levels_gained = 0
        while player.experience >= 100:
            player.experience -= 100
            player.level += 1
            player.max_health += 10
            player.health = player.max_health
            levels_gained += 1
        
        db.commit()
        
        result = {
            "updated": True,
            "player": player.name,
            "exp_gained": exp_change,
            "current_exp": player.experience,
            "level": player.level
        }
        
        if levels_gained > 0:
            result["leveled_up"] = True
            result["levels_gained"] = levels_gained
            result["new_max_health"] = player.max_health
        
        return result
    finally:
        db.close()


@tool
def get_items_at_location(location_id: int) -> List[dict]:
    """Get all item instances at a location (items on the ground).
    
    Returns instance_id which you need for transfer_item or pickup_item.
    """
    db = SessionLocal()
    try:
        items = db.query(ItemInstance).filter(
            ItemInstance.location_id == location_id,
            ItemInstance.owner_type == OwnerType.NONE
        ).all()
        
        result = []
        for item in items:
            template = db.query(ItemTemplate).filter(ItemTemplate.id == item.template_id).first()
            result.append({
                "instance_id": item.id,
                "template_id": item.template_id,
                "name": item.custom_name or (template.name if template else "Unknown"),
                "quantity": item.quantity,
                "rarity": template.rarity.value if template and template.rarity else None,
                "buffs": item.buffs or [],
                "flaws": item.flaws or []
            })
        return result
    finally:
        db.close()


@tool
def get_player_inventory(player_id: int) -> List[dict]:
    """Get all items in a player's inventory.
    
    Returns instance_id which you need for transfer_item (to give/drop items).
    """
    db = SessionLocal()
    try:
        items = db.query(ItemInstance).filter(
            ItemInstance.owner_type == OwnerType.PC,
            ItemInstance.owner_id == player_id
        ).all()
        
        result = []
        for item in items:
            template = db.query(ItemTemplate).filter(ItemTemplate.id == item.template_id).first()
            result.append({
                "instance_id": item.id,
                "template_id": item.template_id,
                "name": item.custom_name or (template.name if template else "Unknown"),
                "quantity": item.quantity,
                "is_equipped": item.is_equipped,
                "rarity": template.rarity.value if template and template.rarity else None,
                "buffs": item.buffs or [],
                "flaws": item.flaws or []
            })
        return result
    finally:
        db.close()


@tool
def get_npc_inventory(npc_id: int) -> List[dict]:
    """Get all items in an NPC's inventory.
    
    Returns instance_id which you need for transfer_item (for looting/trading).
    """
    db = SessionLocal()
    try:
        items = db.query(ItemInstance).filter(
            ItemInstance.owner_type == OwnerType.NPC,
            ItemInstance.owner_id == npc_id
        ).all()
        
        result = []
        for item in items:
            template = db.query(ItemTemplate).filter(ItemTemplate.id == item.template_id).first()
            result.append({
                "instance_id": item.id,
                "template_id": item.template_id,
                "name": item.custom_name or (template.name if template else "Unknown"),
                "quantity": item.quantity,
                "rarity": template.rarity.value if template and template.rarity else None,
                "buffs": item.buffs or [],
                "flaws": item.flaws or []
            })
        return result
    finally:
        db.close()


@tool
def pickup_item(player_id: int, item_instance_id: int) -> dict:
    """Player picks up an item from the ground.
    
    Convenience wrapper for transfer_item. Use get_items_at_location first to find instance_id.
    """
    db = SessionLocal()
    try:
        item = db.query(ItemInstance).filter(ItemInstance.id == item_instance_id).first()
        if not item:
            return {"error": f"Item instance {item_instance_id} not found"}
        
        if item.owner_type != OwnerType.NONE:
            return {"error": "Item is not on the ground - it belongs to someone"}
        
        player = db.query(PlayerCharacter).filter(PlayerCharacter.id == player_id).first()
        if not player:
            return {"error": f"Player {player_id} not found"}
        
        template = db.query(ItemTemplate).filter(ItemTemplate.id == item.template_id).first()
        item_name = item.custom_name or (template.name if template else "Unknown")
        
        item.owner_type = OwnerType.PC
        item.owner_id = player_id
        item.location_id = None
        db.commit()
        
        return {
            "picked_up": True,
            "item": item_name,
            "instance_id": item.id,
            "quantity": item.quantity,
            "player": player.name
        }
    finally:
        db.close()


@tool
def drop_item(player_id: int, item_instance_id: int, location_id: int) -> dict:
    """Player drops an item from inventory onto the ground at a location.
    
    Use get_player_inventory first to find instance_id.
    """
    db = SessionLocal()
    try:
        item = db.query(ItemInstance).filter(ItemInstance.id == item_instance_id).first()
        if not item:
            return {"error": f"Item instance {item_instance_id} not found"}
        
        if item.owner_type != OwnerType.PC or item.owner_id != player_id:
            return {"error": "Item is not in this player's inventory"}
        
        location = db.query(Location).filter(Location.id == location_id).first()
        if not location:
            return {"error": f"Location {location_id} not found"}
        
        template = db.query(ItemTemplate).filter(ItemTemplate.id == item.template_id).first()
        item_name = item.custom_name or (template.name if template else "Unknown")
        
        item.owner_type = OwnerType.NONE
        item.owner_id = None
        item.location_id = location_id
        item.is_equipped = False
        db.commit()
        
        return {
            "dropped": True,
            "item": item_name,
            "instance_id": item.id,
            "location": location.name
        }
    finally:
        db.close()


@tool
def set_companion_follow(npc_id: int, player_id: int) -> dict:
    """Make an NPC follow a player as a companion.
    
    The NPC will automatically move with the player when they change locations.
    Use this when an NPC agrees to join the player or is recruited.
    The NPC should be willing (positive relationship/disposition) or have story reason.
    """
    db = SessionLocal()
    try:
        npc = db.query(NonPlayerCharacter).filter(NonPlayerCharacter.id == npc_id).first()
        if not npc:
            return {"error": f"NPC with id {npc_id} not found"}
        
        player = db.query(PlayerCharacter).filter(PlayerCharacter.id == player_id).first()
        if not player:
            return {"error": f"Player with id {player_id} not found"}
        
        # Set NPC to follow player and move to player's location
        npc.following_player_id = player_id
        npc.location_id = player.current_location_id
        db.commit()
        
        return {
            "success": True,
            "companion": npc.name,
            "now_following": player.name,
            "message": f"{npc.name} is now following {player.name}"
        }
    finally:
        db.close()


@tool
def dismiss_companion(npc_id: int) -> dict:
    """Stop an NPC from following a player.
    
    Use when player tells a companion to stay, wait, or leave.
    The NPC will remain at their current location.
    """
    db = SessionLocal()
    try:
        npc = db.query(NonPlayerCharacter).filter(NonPlayerCharacter.id == npc_id).first()
        if not npc:
            return {"error": f"NPC with id {npc_id} not found"}
        
        if not npc.following_player_id:
            return {"error": f"{npc.name} is not currently following anyone"}
        
        player = db.query(PlayerCharacter).filter(PlayerCharacter.id == npc.following_player_id).first()
        player_name = player.name if player else "the player"
        
        npc.following_player_id = None
        db.commit()
        
        location = db.query(Location).filter(Location.id == npc.location_id).first()
        location_name = location.name if location else "their current location"
        
        return {
            "success": True,
            "companion": npc.name,
            "stayed_at": location_name,
            "message": f"{npc.name} will wait at {location_name}"
        }
    finally:
        db.close()


@tool
def get_player_companions(player_id: int) -> List[dict]:
    """Get all NPCs currently following a player as companions."""
    db = SessionLocal()
    try:
        companions = db.query(NonPlayerCharacter).filter(
            NonPlayerCharacter.following_player_id == player_id
        ).all()
        
        return [{
            "id": npc.id,
            "name": npc.name,
            "type": npc.npc_type,
            "health": npc.health,
            "max_health": npc.max_health,
            "behavior": npc.behavior_state.value if npc.behavior_state else "passive"
        } for npc in companions]
    finally:
        db.close()


@tool
def search_memories(player_id: int, query: str) -> List[dict]:
    """Search through past session memories for relevant information.
    
    Use this when the player references something from the past, like:
    - A person they met before ("remember Bob?")
    - A place they visited ("that cave we explored")
    - An event ("when we fought the dragon")
    - A promise or unfinished business ("the debt I owe")
    
    Returns summaries of relevant past sessions with context.
    """
    from .memory_manager import get_memory_manager
    
    memory_manager = get_memory_manager()
    results = memory_manager.search_memories(player_id, query, limit=3)
    
    if not results:
        return [{"message": "No relevant memories found for this query"}]
    
    return results


@tool
def recall_session_details(session_id: str) -> dict:
    """Get detailed information about a specific past session.
    
    Use this after search_memories finds a relevant session and you need more context.
    Returns the session summary plus recent messages from that session.
    """
    from .memory_manager import get_memory_manager
    
    memory_manager = get_memory_manager()
    return memory_manager.get_session_details(session_id, message_limit=10)


# ============= Region Tools =============

@tool
def get_region_info(region_id: int) -> dict:
    """Get detailed information about a region including its characteristics.
    
    Returns region description, dominant races, wealth, climate, political structure,
    danger level, and notable features.
    """
    db = SessionLocal()
    try:
        region = db.query(Region).filter(Region.id == region_id).first()
        if not region:
            return {"error": f"Region with id {region_id} not found"}
        
        # Get locations in this region
        locations = db.query(Location).filter(Location.region_id == region_id).all()
        
        return {
            "id": region.id,
            "name": region.name,
            "description": region.description,
            "dominant_races": region.dominant_race_description,
            "wealth_level": region.wealth_level.value if region.wealth_level else None,
            "wealth_description": region.wealth_description,
            "climate": region.climate.value if region.climate else None,
            "terrain": region.terrain_description,
            "political": region.political_description,
            "danger_level": region.danger_level.value if region.danger_level else None,
            "threats": region.threats_description,
            "history": region.history_description,
            "notable_features": region.notable_features,
            "locations": [{"id": loc.id, "name": loc.name, "type": loc.location_type} for loc in locations]
        }
    finally:
        db.close()


@tool
def list_regions() -> List[dict]:
    """Get a list of all regions in the world."""
    db = SessionLocal()
    try:
        regions = db.query(Region).all()
        return [{
            "id": r.id,
            "name": r.name,
            "climate": r.climate.value if r.climate else None,
            "wealth_level": r.wealth_level.value if r.wealth_level else None,
            "danger_level": r.danger_level.value if r.danger_level else None
        } for r in regions]
    finally:
        db.close()


@tool
def create_region(name: str, description: str,
                  dominant_race_description: Optional[str] = None,
                  wealth_level: str = "modest",
                  wealth_description: Optional[str] = None,
                  climate: str = "temperate",
                  terrain_description: Optional[str] = None,
                  political_description: Optional[str] = None,
                  danger_level: str = "low",
                  threats_description: Optional[str] = None,
                  history_description: Optional[str] = None,
                  notable_features: Optional[str] = None) -> dict:
    """Create a new region in the world.
    
    Regions contain multiple locations and define their shared characteristics.
    Use region info to guide location and NPC creation within it.
    
    wealth_level: destitute, poor, modest, prosperous, opulent
    climate: temperate, tropical, arid, arctic, mountainous, coastal, swamp, forest
    danger_level: safe, low, moderate, high, deadly
    """
    db = SessionLocal()
    try:
        # Convert string enums
        try:
            wealth = WealthLevel(wealth_level)
        except ValueError:
            wealth = WealthLevel.MODEST
        
        try:
            clim = ClimateType(climate)
        except ValueError:
            clim = ClimateType.TEMPERATE
        
        try:
            danger = DangerLevel(danger_level)
        except ValueError:
            danger = DangerLevel.LOW
        
        region = Region(
            name=name,
            description=description,
            dominant_race_description=dominant_race_description,
            wealth_level=wealth,
            wealth_description=wealth_description,
            climate=clim,
            terrain_description=terrain_description,
            political_description=political_description,
            danger_level=danger,
            threats_description=threats_description,
            history_description=history_description,
            notable_features=notable_features
        )
        db.add(region)
        db.commit()
        db.refresh(region)
        
        return {
            "created": True,
            "region_id": region.id,
            "name": region.name
        }
    finally:
        db.close()


@tool
def update_region(region_id: int,
                  description: Optional[str] = None,
                  threats_description: Optional[str] = None,
                  danger_level: Optional[str] = None,
                  notable_features: Optional[str] = None) -> dict:
    """Update a region's properties.
    
    Use to evolve regions over time - e.g., after major events change danger levels.
    """
    db = SessionLocal()
    try:
        region = db.query(Region).filter(Region.id == region_id).first()
        if not region:
            return {"error": f"Region with id {region_id} not found"}
        
        if description:
            region.description = description
        if threats_description:
            region.threats_description = threats_description
        if danger_level:
            try:
                region.danger_level = DangerLevel(danger_level)
            except ValueError:
                pass
        if notable_features:
            region.notable_features = notable_features
        
        db.commit()
        return {"updated": True, "region_id": region_id, "name": region.name}
    finally:
        db.close()


@tool
def assign_location_to_region(location_id: int, region_id: int) -> dict:
    """Assign a location to a region.
    
    Locations inherit regional context (climate, races, wealth, danger).
    """
    db = SessionLocal()
    try:
        location = db.query(Location).filter(Location.id == location_id).first()
        if not location:
            return {"error": f"Location with id {location_id} not found"}
        
        region = db.query(Region).filter(Region.id == region_id).first()
        if not region:
            return {"error": f"Region with id {region_id} not found"}
        
        location.region_id = region_id
        db.commit()
        
        return {
            "assigned": True,
            "location": location.name,
            "region": region.name
        }
    finally:
        db.close()


# =============================================================================
# RACE MANAGEMENT TOOLS
# =============================================================================

@tool
def list_races() -> list:
    """List all available races in the world.
    
    Use this to see what races exist before creating NPCs or when storytelling
    involves racial dynamics (e.g., encountering orcs, elves, etc.)
    """
    db = SessionLocal()
    try:
        races = db.query(Race).all()
        return [{
            "id": r.id,
            "name": r.name,
            "description": r.description
        } for r in races]
    finally:
        db.close()


@tool
def get_race_relationships(race_id: Optional[int] = None) -> list:
    """Get racial relationship modifiers between races.
    
    Args:
        race_id: If provided, get relationships for this race only. Otherwise get all.
    
    Returns relationships with modifiers (-100 to 100) and reasons.
    Example: Dwarves and Elves might have -20 modifier due to ancient grudges.
    """
    db = SessionLocal()
    try:
        query = db.query(RaceRelationship)
        if race_id:
            query = query.filter(
                (RaceRelationship.race_source_id == race_id) | 
                (RaceRelationship.race_target_id == race_id)
            )
        relationships = query.all()
        
        results = []
        for rel in relationships:
            source = db.query(Race).filter(Race.id == rel.race_source_id).first()
            target = db.query(Race).filter(Race.id == rel.race_target_id).first()
            results.append({
                "source_race": source.name if source else None,
                "target_race": target.name if target else None,
                "modifier": rel.base_relationship_modifier,
                "reason": rel.reason
            })
        return results
    finally:
        db.close()


@tool
def create_race(name: str, description: str) -> dict:
    """Create a new race in the world.
    
    Use when the story introduces a race that doesn't exist yet (e.g., Orcs, Goblins).
    Check list_races() first to avoid duplicates!
    """
    db = SessionLocal()
    try:
        # Check for existing
        existing = db.query(Race).filter(Race.name.ilike(name)).first()
        if existing:
            return {"error": f"Race '{name}' already exists", "existing_id": existing.id}
        
        race = Race(name=name, description=description)
        db.add(race)
        db.commit()
        db.refresh(race)
        
        return {
            "created": True,
            "race_id": race.id,
            "name": race.name
        }
    finally:
        db.close()


@tool
def update_race_relationship(source_race_id: int, target_race_id: int, 
                             modifier: int, reason: Optional[str] = None) -> dict:
    """Set or update the relationship modifier between two races.
    
    Args:
        source_race_id: First race ID
        target_race_id: Second race ID  
        modifier: Relationship modifier (-100 hostile to +100 allied)
        reason: Why this relationship exists (e.g., "Ancient war", "Trade partners")
    
    This affects how NPCs of these races initially react to each other.
    """
    db = SessionLocal()
    try:
        # Validate races exist
        source = db.query(Race).filter(Race.id == source_race_id).first()
        target = db.query(Race).filter(Race.id == target_race_id).first()
        if not source or not target:
            return {"error": "One or both races not found"}
        
        # Find existing or create new
        rel = db.query(RaceRelationship).filter(
            RaceRelationship.race_source_id == source_race_id,
            RaceRelationship.race_target_id == target_race_id
        ).first()
        
        if rel:
            rel.base_relationship_modifier = modifier
            if reason:
                rel.reason = reason
        else:
            rel = RaceRelationship(
                race_source_id=source_race_id,
                race_target_id=target_race_id,
                base_relationship_modifier=modifier,
                reason=reason
            )
            db.add(rel)
        
        db.commit()
        
        return {
            "updated": True,
            "source_race": source.name,
            "target_race": target.name,
            "modifier": modifier,
            "reason": reason
        }
    finally:
        db.close()


# ============= Combat Tools =============

@tool
def initiate_combat(player_id: int, description: str,
                    player_team_ids: Optional[List[int]] = None,
                    enemy_team_ids: Optional[List[int]] = None) -> dict:
    """Start a combat encounter between two teams.

    Parameter meaning is intentionally explicit:

    - `player_id`: The *owner player* whose combat session is being created/tracked.
      (We key active combats by player_id, so all combat tools take it.)
    - `player_team_ids`: Optional list of ALLY NPC ids on the player's side.
      The owning player character is implied by `player_id` and is automatically included.
    - `enemy_team_ids`: Required list of ENEMY NPC ids.

    Returns:
        Combat session info with full team stats.

    Example:
        initiate_combat(
            player_id=1,
            description="Goblin ambush",
            player_team_ids=[5],
            enemy_team_ids=[10, 11],
        )
    """
    db = SessionLocal()
    try:
        if player_id <= 0:
            return {"error": "player_id must be a positive integer"}

        if player_team_ids is None:
            player_team_ids = []
        if enemy_team_ids is None:
            enemy_team_ids = []

        if not isinstance(player_team_ids, list) or not isinstance(enemy_team_ids, list):
            return {"error": "player_team_ids and enemy_team_ids must be lists of integers"}

        player = db.query(PlayerCharacter).filter(PlayerCharacter.id == player_id).first()
        if not player:
            return {"error": f"Player with id {player_id} not found"}

        if len(enemy_team_ids) == 0:
            nearby = []
            if player.current_location_id:
                npcs = db.query(NonPlayerCharacter).filter(
                    NonPlayerCharacter.location_id == player.current_location_id
                ).all()
                nearby = [{"id": n.id, "name": n.name, "type": n.npc_type} for n in npcs]
            return {
                "error": "enemy_team_ids is required and must contain at least one NPC id",
                "example": {
                    "player_id": player_id,
                    "description": description,
                    "player_team_ids": player_team_ids,
                    "enemy_team_ids": [npc["id"] for npc in nearby[:3]] if nearby else [0]
                },
                "nearby_npcs": nearby
            }

        # Check for existing active combat
        existing = db.query(CombatSession).filter(
            CombatSession.player_id == player_id,
            CombatSession.status == "active"
        ).first()
        if existing:
            return {
                "error": "ALREADY IN COMBAT! Do NOT call initiate_combat again.",
                "hint": "Combat is already active. Just narrate the fight and use update_combat_hp to track damage. Call end_combat when the fight concludes.",
                "combat_id": existing.id,
                "description": existing.description,
                "player_team": existing.team_player,
                "enemy_team": existing.team_enemy
            }
        
        # Build player team with full stats (PC implied by player_id)
        team_player = [{
            "type": "PC", "id": player.id, "name": player.name,
            "hp": player.health, "max_hp": player.max_health,
            "role": "player"
        }]

        for npc_id in player_team_ids:
            if not isinstance(npc_id, int) or npc_id <= 0:
                continue
            npc = db.query(NonPlayerCharacter).filter(NonPlayerCharacter.id == npc_id).first()
            if npc:
                team_player.append({
                    "type": "NPC", "id": npc.id, "name": npc.name,
                    "hp": npc.health, "max_hp": npc.max_health,
                    "role": "ally"
                })
        
        # Build enemy team with full stats
        team_enemy = []
        for npc_id in enemy_team_ids:
            if not isinstance(npc_id, int) or npc_id <= 0:
                continue
            npc = db.query(NonPlayerCharacter).filter(NonPlayerCharacter.id == npc_id).first()
            if npc:
                team_enemy.append({
                    "type": "NPC", "id": npc.id, "name": npc.name,
                    "hp": npc.health, "max_hp": npc.max_health,
                    "role": "enemy"
                })
        
        if not team_enemy:
            return {"error": "No valid combatants on enemy team"}
        
        # Create combat session
        combat = CombatSession(
            player_id=player_id,
            status="active",
            description=description,
            team_player=team_player,
            team_enemy=team_enemy
        )
        db.add(combat)
        db.commit()
        db.refresh(combat)
        
        return {
            "combat_started": True,
            "combat_id": combat.id,
            "description": description,
            "player_team": team_player,
            "enemy_team": team_enemy,
            "message": "Combat initiated! Track damage with update_player_health/update_npc_health. Use add_combatant/remove_combatant to modify teams. End with end_combat."
        }
    finally:
        db.close()


@tool
def get_active_combat(player_id: int) -> dict:
    """Get the current active combat for a player, if any.

    Args:
        player_id: The *owner player* whose combat session should be checked.

    Returns:
        Combat state with both teams and their current HP.
    """
    db = SessionLocal()
    try:
        if player_id <= 0:
            return {"error": "player_id must be a positive integer"}

        combat = db.query(CombatSession).filter(
            CombatSession.player_id == player_id,
            CombatSession.status == "active"
        ).first()
        
        if not combat:
            return {"in_combat": False}
        
        return {
            "in_combat": True,
            "combat_id": combat.id,
            "description": combat.description,
            "player_team": combat.team_player,
            "enemy_team": combat.team_enemy
        }
    finally:
        db.close()


@tool
def add_combatant(player_id: int, char_type: str, char_id: int, team: str) -> dict:
    """Add a combatant to an active combat.

    Args:
        player_id: The *owner player* whose active combat session is being modified.
        char_type: The combatant type: "PC" or "NPC".
        char_id: The ID of that character. If `char_type` is "PC", this is `PlayerCharacter.id`.
                If `char_type` is "NPC", this is `NonPlayerCharacter.id`.
        team: Which side to join: "player" (allies) or "enemy".

    Example:
        add_combatant(player_id=1, char_type="NPC", char_id=15, team="enemy")
    """
    db = SessionLocal()
    try:
        if player_id <= 0:
            return {"error": "player_id must be a positive integer"}
        if team not in ("player", "enemy"):
            return {"error": "team must be 'player' or 'enemy'"}
        if char_type not in ("PC", "NPC"):
            return {"error": "char_type must be 'PC' or 'NPC'"}
        if char_id <= 0:
            return {"error": "char_id must be a positive integer"}

        combat = db.query(CombatSession).filter(
            CombatSession.player_id == player_id,
            CombatSession.status == "active"
        ).first()
        
        if not combat:
            return {"error": "No active combat"}
        
        # Check if already in combat
        if combat.get_combatant(char_type, char_id):
            return {"error": f"{char_type} {char_id} is already in combat"}
        
        # Get character stats
        member = None
        if char_type == "PC":
            pc = db.query(PlayerCharacter).filter(PlayerCharacter.id == char_id).first()
            if pc:
                member = {"type": "PC", "id": pc.id, "name": pc.name,
                         "hp": pc.health, "max_hp": pc.max_health, "role": "player" if team == "player" else "enemy"}
        elif char_type == "NPC":
            npc = db.query(NonPlayerCharacter).filter(NonPlayerCharacter.id == char_id).first()
            if npc:
                member = {"type": "NPC", "id": npc.id, "name": npc.name,
                         "hp": npc.health, "max_hp": npc.max_health, "role": "ally" if team == "player" else "enemy"}
        
        if not member:
            return {"error": f"{char_type} {char_id} not found"}
        
        # Add to appropriate team
        if team == "player":
            team_list = list(combat.team_player or [])
            team_list.append(member)
            combat.team_player = team_list
        else:
            team_list = list(combat.team_enemy or [])
            team_list.append(member)
            combat.team_enemy = team_list
        
        db.commit()
        
        return {
            "added": True,
            "name": member["name"],
            "team": team,
            "combat_id": combat.id
        }
    finally:
        db.close()


@tool
def remove_combatant(player_id: int, char_type: str, char_id: int, reason: str = "fled") -> dict:
    """Remove a combatant from active combat (fled, captured, etc).

    Args:
        player_id: The *owner player* whose active combat session is being modified.
        char_type: "PC" or "NPC".
        char_id: The ID of the character to remove (PC id or NPC id depending on char_type).
        reason: Why they left ("fled", "captured", "retreated", "died").
    """
    db = SessionLocal()
    try:
        if player_id <= 0:
            return {"error": "player_id must be a positive integer"}
        if char_type not in ("PC", "NPC"):
            return {"error": "char_type must be 'PC' or 'NPC'"}
        if char_id <= 0:
            return {"error": "char_id must be a positive integer"}

        combat = db.query(CombatSession).filter(
            CombatSession.player_id == player_id,
            CombatSession.status == "active"
        ).first()
        
        if not combat:
            return {"error": "No active combat"}
        
        # Find and remove from player team
        removed_name = None
        team_player = list(combat.team_player or [])
        for i, m in enumerate(team_player):
            if m.get("type") == char_type and m.get("id") == char_id:
                removed_name = m.get("name")
                team_player.pop(i)
                combat.team_player = team_player
                break
        
        # Find and remove from enemy team
        if not removed_name:
            team_enemy = list(combat.team_enemy or [])
            for i, m in enumerate(team_enemy):
                if m.get("type") == char_type and m.get("id") == char_id:
                    removed_name = m.get("name")
                    team_enemy.pop(i)
                    combat.team_enemy = team_enemy
                    break
        
        if not removed_name:
            return {"error": f"{char_type} {char_id} not found in combat"}
        
        db.commit()
        
        return {
            "removed": True,
            "name": removed_name,
            "reason": reason,
            "combat_id": combat.id
        }
    finally:
        db.close()


@tool
def update_combat_hp(player_id: int, char_type: str, char_id: int, new_hp: int) -> dict:
    """Update a combatant's HP in the combat tracker (keeps combat state in sync).

    Why both `player_id` and `char_id`?
    - `player_id` identifies *which active combat session* to modify.
      (Combats are tracked per-player.)
    - (`char_type`, `char_id`) identifies *which combatant* inside that combat.

    This updates BOTH the database character record AND the combat tracker.

    Args:
        player_id: The *owner player* whose active combat session is being updated.
        char_type: "PC" or "NPC".
        char_id: The ID of the combatant (PC id or NPC id depending on char_type).
        new_hp: New HP value (will be clamped to >= 0).
    """
    db = SessionLocal()
    try:
        if player_id <= 0:
            return {"error": "player_id must be a positive integer"}
        if char_type not in ("PC", "NPC"):
            return {"error": "char_type must be 'PC' or 'NPC'"}
        if char_id <= 0:
            return {"error": "char_id must be a positive integer"}

        combat = db.query(CombatSession).filter(
            CombatSession.player_id == player_id,
            CombatSession.status == "active"
        ).first()
        
        if not combat:
            return {"error": "No active combat"}
        
        # Update actual character
        if char_type == "PC":
            char = db.query(PlayerCharacter).filter(PlayerCharacter.id == char_id).first()
            if char:
                char.health = max(0, new_hp)
        elif char_type == "NPC":
            char = db.query(NonPlayerCharacter).filter(NonPlayerCharacter.id == char_id).first()
            if char:
                char.health = max(0, new_hp)
        
        # Update combat tracker
        updated_name = None
        team_player = list(combat.team_player or [])
        for m in team_player:
            if m.get("type") == char_type and m.get("id") == char_id:
                m["hp"] = max(0, new_hp)
                updated_name = m.get("name")
                combat.team_player = team_player
                break
        
        if not updated_name:
            team_enemy = list(combat.team_enemy or [])
            for m in team_enemy:
                if m.get("type") == char_type and m.get("id") == char_id:
                    m["hp"] = max(0, new_hp)
                    updated_name = m.get("name")
                    combat.team_enemy = team_enemy
                    break
        
        if not updated_name:
            return {"error": f"{char_type} {char_id} not found in combat"}
        
        db.commit()
        
        status = "DOWN" if new_hp <= 0 else "standing"
        return {
            "updated": True,
            "name": updated_name,
            "new_hp": max(0, new_hp),
            "status": status
        }
    finally:
        db.close()


@tool
def end_combat(player_id: int, outcome: str, summary: str) -> dict:
    """End an active combat encounter.

    Args:
        player_id: The *owner player* whose active combat session is being ended.
        outcome: Result of combat ("victory", "defeat", "fled", "negotiated", "interrupted").
        summary: A cinematic, in-world narrative summary that blends into the story.
            Write it as a tight story beat (prefer ~4-8 sentences) that clearly conveys
            the turning point, decisive moment, and immediate aftermath, ending with a
            small forward hook. No meta headers like "COMBAT SUMMARY" and no bullet-point
            recaps. This summary will replace the individual combat messages in the story log.

    Returns:
        Final combat state and confirmation.
    """
    db = SessionLocal()
    try:
        if player_id <= 0:
            return {"error": "player_id must be a positive integer"}

        combat = db.query(CombatSession).filter(
            CombatSession.player_id == player_id,
            CombatSession.status == "active"
        ).first()
        
        if not combat:
            return {"error": "No active combat to end"}
        
        combat_id = combat.id
        combat.status = "ended"
        combat.outcome = outcome
        combat.summary = summary
        combat.ended_at = datetime.utcnow()
        
        db.commit()
        
        # Compress combat messages into a single summary
        story_manager = get_story_manager()
        combat_tag = f"combat:{combat_id}"
        
        # Store only narrative text so it reads like part of the story
        compressed_summary = summary
        
        messages_compressed = story_manager.compress_tagged_messages(
            player_id=player_id,
            tag=combat_tag,
            summary=compressed_summary,
            summary_tags=[f"combat:{combat_id}:summary", "combat_summary", f"combat_outcome:{outcome}"]
        )
        
        return {
            "combat_ended": True,
            "combat_id": combat_id,
            "outcome": outcome,
            "summary": summary,
            "final_player_team": combat.team_player,
            "final_enemy_team": combat.team_enemy,
            "messages_compressed": messages_compressed
        }
    finally:
        db.close()


def get_game_tools():
    """Return all tools available to the Game Master agent."""
    return [
        # Query tools
        get_player_info,
        get_location_info,
        get_npc_info,
        get_npcs_at_location,
        get_relationship,
        get_player_quests,
        list_item_templates,
        # Inventory query tools (IMPORTANT: use these to get instance_ids)
        get_items_at_location,
        get_player_inventory,
        get_npc_inventory,
        # Long-term memory (search past sessions)
        search_memories,
        recall_session_details,
        # Player management
        update_player_health,
        update_player_gold,
        update_player_experience,
        move_player,
        # Item transfer (use instance_id from inventory queries)
        pickup_item,
        drop_item,
        transfer_item,
        consume_item_instance,
        # Item creation (creates NEW items - use sparingly for rewards/loot)
        create_item_for_player,
        create_item_for_npc,
        spawn_item_at_location,
        # NPC management
        move_npc,
        update_npc_health,
        update_npc_behavior,
        update_npc_disposition,
        create_npc,
        # Companion management
        set_companion_follow,
        dismiss_companion,
        get_player_companions,
        # Relationship management
        update_relationship,
        # Quest management
        create_quest,
        update_quest_status,
        # World building
        list_locations,
        create_location,
        create_item_template,
        # Region management
        get_region_info,
        list_regions,
        create_region,
        update_region,
        assign_location_to_region,
        # Race management
        list_races,
        get_race_relationships,
        create_race,
        update_race_relationship,
        # Combat management
        initiate_combat,
        get_active_combat,
        add_combatant,
        remove_combatant,
        update_combat_hp,
        end_combat
    ]
