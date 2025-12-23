"""
Database seed script - Populates the database with initial game data.

Run manually: python seed.py
Or import and call: from seed import seed_database; seed_database()
"""

from sqlalchemy.orm import Session
from database import SessionLocal, engine
from models import (
    Location, Race, RaceRelationship, Faction, NonPlayerCharacter,
    BehaviorState, AlignmentType, ItemTemplate, ItemCategory, ItemRarity
)


def seed_database():
    """Seed the database with initial game data."""
    db = SessionLocal()
    
    try:
        # Check if already seeded
        if db.query(Location).first():
            print("Database already seeded. Skipping...")
            return False
        
        print("Seeding database...")
        
        # === LOCATIONS ===
        tavern = Location(
            name="The Rusty Tankard",
            description="A cozy tavern with a roaring fireplace. The smell of ale and roasted meat fills the air. Adventurers gather here to share tales and find work.",
            location_type="tavern"
        )
        forest = Location(
            name="Whispering Woods",
            description="An ancient forest shrouded in mist. Twisted oaks loom overhead, their branches creaking in an unfelt wind. Strange lights flicker between the trees.",
            location_type="wilderness"
        )
        db.add_all([tavern, forest])
        db.flush()
        print(f"  ✓ Created locations: {tavern.name}, {forest.name}")
        
        # === RACES ===
        human = Race(
            name="Human",
            description="Versatile and ambitious, humans are the most common folk in the realm. They adapt quickly and forge alliances with ease."
        )
        elf = Race(
            name="Elf",
            description="Ancient and graceful, elves live for centuries and have deep connections to nature and magic. They are wary of outsiders."
        )
        dwarf = Race(
            name="Dwarf",
            description="Stout and sturdy, dwarves are master craftsmen who dwell in mountain strongholds. They value honor and tradition above all."
        )
        db.add_all([human, elf, dwarf])
        db.flush()
        print(f"  ✓ Created races: Human, Elf, Dwarf")
        
        # === RACE RELATIONSHIPS ===
        race_relations = [
            RaceRelationship(
                race_source_id=human.id,
                race_target_id=elf.id,
                base_relationship_modifier=10,
                reason="Humans admire elven culture and magic"
            ),
            RaceRelationship(
                race_source_id=elf.id,
                race_target_id=human.id,
                base_relationship_modifier=-10,
                reason="Elves find humans reckless and short-sighted"
            ),
            RaceRelationship(
                race_source_id=human.id,
                race_target_id=dwarf.id,
                base_relationship_modifier=20,
                reason="Humans and dwarves have strong trade relations"
            ),
            RaceRelationship(
                race_source_id=dwarf.id,
                race_target_id=human.id,
                base_relationship_modifier=15,
                reason="Dwarves respect human industriousness"
            ),
            RaceRelationship(
                race_source_id=elf.id,
                race_target_id=dwarf.id,
                base_relationship_modifier=-20,
                reason="Ancient grudges over forest-clearing for mines"
            ),
            RaceRelationship(
                race_source_id=dwarf.id,
                race_target_id=elf.id,
                base_relationship_modifier=-15,
                reason="Dwarves see elves as arrogant and impractical"
            ),
        ]
        db.add_all(race_relations)
        print(f"  ✓ Created {len(race_relations)} race relationships")
        
        # === FACTIONS ===
        merchants_guild = Faction(
            name="Merchants Guild",
            description="A powerful coalition of traders and shopkeepers who control commerce in the region. They value profit but maintain fair dealings.",
            alignment=AlignmentType.LAWFUL
        )
        db.add(merchants_guild)
        db.flush()
        print(f"  ✓ Created faction: {merchants_guild.name}")
        
        # === NPCs ===
        innkeeper = NonPlayerCharacter(
            name="Greta Ironbrew",
            npc_type="merchant",
            health=40,
            max_health=40,
            behavior_state=BehaviorState.PASSIVE,
            base_disposition=30,
            description="A stout dwarven woman with braided auburn hair and a warm smile. She runs the Rusty Tankard with an iron fist and a generous heart.",
            dialogue="Welcome to the Rusty Tankard, traveler! Sit, drink, and tell me your tale.",
            location_id=tavern.id,
            race_id=dwarf.id,
            faction_id=merchants_guild.id,
            personality_traits={
                "friendly": True,
                "shrewd": True,
                "protective_of_patrons": True,
                "loves_gossip": True
            }
        )
        db.add(innkeeper)
        print(f"  ✓ Created NPC: {innkeeper.name}")
        
        # === ITEM TEMPLATES ===
        item_templates = [
            ItemTemplate(
                name="Iron Sword",
                category=ItemCategory.WEAPON,
                description="A sturdy blade forged from iron. Reliable and widely used by soldiers and adventurers alike.",
                weight=3,
                rarity=ItemRarity.COMMON,
                properties={"damage": 5, "type": "melee", "two_handed": False}
            ),
            ItemTemplate(
                name="Healing Potion",
                category=ItemCategory.POTION,
                description="A small vial of red liquid that restores health when consumed.",
                weight=1,
                rarity=ItemRarity.COMMON,
                properties={"heal_amount": 25, "consumable": True}
            ),
            ItemTemplate(
                name="Bread",
                category=ItemCategory.FOOD,
                description="A fresh loaf of crusty bread. Simple but filling.",
                weight=1,
                rarity=ItemRarity.COMMON,
                properties={"nutrition": 10, "consumable": True}
            ),
            ItemTemplate(
                name="Torch",
                category=ItemCategory.MISC,
                description="A wooden stick wrapped in oil-soaked cloth. Provides light in dark places.",
                weight=1,
                rarity=ItemRarity.COMMON,
                properties={"light_radius": 10, "burn_time_minutes": 60}
            ),
            ItemTemplate(
                name="Traveler's Cape",
                category=ItemCategory.ARMOR,
                description="A simple woolen cape that provides warmth and protection from the elements.",
                weight=2,
                rarity=ItemRarity.COMMON,
                properties={"defense": 1, "warmth": 5, "slot": "back"}
            ),
        ]
        db.add_all(item_templates)
        print(f"  ✓ Created {len(item_templates)} item templates")
        
        db.commit()
        print("\n✓ Database seeded successfully!")
        return True
        
    except Exception as e:
        db.rollback()
        print(f"\n✗ Error seeding database: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
