from typing import Optional, List
from langchain_core.tools import tool
from sqlalchemy.orm import Session

from database import SessionLocal
from models import (
    PlayerCharacter, NonPlayerCharacter, Location, Quest,
    ItemTemplate, ItemInstance, Race, Faction,
    CharacterRelationship, CharacterType, OwnerType
)


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
    """Get the relationship between two characters. Types are 'PC' or 'NPC'."""
    db = SessionLocal()
    try:
        src_type = CharacterType.PC if source_type.upper() == "PC" else CharacterType.NPC
        tgt_type = CharacterType.PC if target_type.upper() == "PC" else CharacterType.NPC
        
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
    """Update or create a relationship between two characters. value_change is added to current value (-100 to 100 range)."""
    db = SessionLocal()
    try:
        src_type = CharacterType.PC if source_type.upper() == "PC" else CharacterType.NPC
        tgt_type = CharacterType.PC if target_type.upper() == "PC" else CharacterType.NPC
        
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
def create_item_for_player(player_id: int, template_id: int, quantity: int = 1, custom_name: Optional[str] = None) -> dict:
    """CREATE a NEW item instance from a template and give it to a player.
    
    WARNING: This creates items out of thin air. Use only for rewards, loot drops, or quest items.
    To transfer an EXISTING item, use transfer_item with the item's instance_id instead.
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
            custom_name=custom_name
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        
        return {
            "given": True,
            "instance_id": item.id,
            "item_name": custom_name or template.name,
            "quantity": quantity,
            "to_player": player.name
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
    """Move a player to a new location."""
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
        db.commit()
        
        return {
            "moved": True,
            "player": player.name,
            "from_location_id": old_location_id,
            "to_location": {"id": location.id, "name": location.name, "description": location.description}
        }
    finally:
        db.close()


@tool
def list_all_locations() -> List[dict]:
    """Get a list of all locations in the game world."""
    db = SessionLocal()
    try:
        locations = db.query(Location).all()
        return [{
            "id": loc.id,
            "name": loc.name,
            "description": loc.description,
            "type": loc.location_type
        } for loc in locations]
    finally:
        db.close()


@tool
def list_item_templates(category: Optional[str] = None) -> List[dict]:
    """List available item templates, optionally filtered by category."""
    db = SessionLocal()
    try:
        query = db.query(ItemTemplate)
        if category:
            query = query.filter(ItemTemplate.category == category)
        
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
    """Create a new NPC in the world."""
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
def create_location(name: str, description: str, location_type: Optional[str] = None) -> dict:
    """Create a new location in the world."""
    db = SessionLocal()
    try:
        location = Location(
            name=name,
            description=description,
            location_type=location_type
        )
        db.add(location)
        db.commit()
        db.refresh(location)
        
        return {
            "created": True,
            "location_id": location.id,
            "name": name
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
                           quantity: int = 1, custom_name: Optional[str] = None) -> dict:
    """Spawn an item on the ground at a location."""
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
            custom_name=custom_name
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        
        return {
            "spawned": True,
            "instance_id": item.id,
            "item_name": custom_name or template.name,
            "location": location.name
        }
    finally:
        db.close()


@tool
def create_item_for_npc(npc_id: int, template_id: int, 
                        quantity: int = 1, custom_name: Optional[str] = None) -> dict:
    """CREATE a NEW item instance from a template and give it to an NPC.
    
    WARNING: This creates items out of thin air. Use only for NPC inventory setup.
    To transfer an EXISTING item, use transfer_item with the item's instance_id instead.
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
            custom_name=custom_name
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        
        return {
            "given": True,
            "instance_id": item.id,
            "item_name": custom_name or template.name,
            "to_npc": npc.name
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
                "rarity": template.rarity.value if template and template.rarity else None
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
                "rarity": template.rarity.value if template and template.rarity else None
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
                "rarity": template.rarity.value if template and template.rarity else None
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
        list_all_locations,
        list_item_templates,
        # Inventory query tools (IMPORTANT: use these to get instance_ids)
        get_items_at_location,
        get_player_inventory,
        get_npc_inventory,
        # Player management
        update_player_health,
        update_player_gold,
        update_player_experience,
        move_player,
        # Item transfer (use instance_id from inventory queries)
        pickup_item,
        drop_item,
        transfer_item,
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
        # Relationship management
        update_relationship,
        # Quest management
        create_quest,
        update_quest_status,
        # World building
        create_location,
        create_item_template
    ]
