"""
Database seed script - Populates the database with initial game data.

Run manually: python seed.py
Or import and call: from seed import seed_database; seed_database()
"""

from sqlalchemy.orm import Session
from database import SessionLocal, engine
from models import (
    Location, Race, RaceRelationship, Faction, NonPlayerCharacter,
    BehaviorState, AlignmentType, ItemTemplate, ItemCategory, ItemRarity,
    Region, ClimateType, WealthLevel, DangerLevel
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
        
        # === REGION ===
        doromir_lowlands = Region(
            name="Doromir Lowlands",
            description="A fertile stretch of rolling farmland and scattered woodlands nestled between the Iron Mountains to the north and the Silvanus Forest to the south. Small villages dot the landscape, connected by well-worn trade roads.",
            dominant_race_description="Predominantly human farming communities with dwarven craftsmen in larger towns. Elven traders occasionally pass through from the southern forests. Halflings run many of the inns along the trade routes.",
            wealth_level=WealthLevel.MODEST,
            wealth_description="The land produces abundant grain and livestock. Most folk live comfortably but simply. The town of Millhaven serves as the regional market, where farmers trade their goods.",
            climate=ClimateType.TEMPERATE,
            terrain_description="Gentle hills covered in wheat fields and pastures. Ancient oak groves mark property boundaries. The River Dor winds lazily through the region, powering watermills.",
            political_description="Under the loose governance of Baron Aldric of Millhaven, who collects modest taxes in exchange for maintaining the roads and a small garrison. Most villages are self-governing with elected elders.",
            danger_level=DangerLevel.LOW,
            threats_description="Wolves grow bold in harsh winters. Goblin bands occasionally raid isolated farms from the northern foothills. Bandits sometimes waylay travelers on lesser-used roads.",
            history_description="Once the borderlands of the ancient Elven kingdom of Silvanus before the Sundering. Human settlers arrived three centuries ago. The ruins of an elven watchtower still stand on Sentinel Hill.",
            notable_features="The Whispering Stones (ancient elven standing stones), Old Mill ruins (haunted according to locals), Sentinel Hill watchtower, The Crossroads Inn (famous meeting point)"
        )
        db.add(doromir_lowlands)
        db.flush()
        print(f"  ✓ Created region: {doromir_lowlands.name}")
        
        # === LOCATIONS (linked to region with modifiers) ===
        tavern = Location(
            name="The Rusty Tankard",
            description="A cozy tavern with a roaring fireplace. The smell of ale and roasted meat fills the air. Adventurers gather here to share tales and find work.",
            location_type="tavern",
            region_id=doromir_lowlands.id,
            danger_modifier=-1,  # Safer than average due to Greta's watchful eye
            wealth_modifier=0,
            population_density="moderate",
            accessibility="public"
        )
        forest = Location(
            name="Whispering Woods",
            description="An ancient forest shrouded in mist. Twisted oaks loom overhead, their branches creaking in an unfelt wind. Strange lights flicker between the trees at night.",
            location_type="wilderness",
            region_id=doromir_lowlands.id,
            danger_modifier=2,  # More dangerous than region average
            climate_override="forest",
            population_density="sparse",
            accessibility="public",
            notes="Locals avoid after dark. Rumors of fey creatures and lost travelers."
        )
        market = Location(
            name="Millhaven Market Square",
            description="The bustling heart of Millhaven town. Merchants hawk wares from wooden stalls while farmers unload carts of produce. The smell of fresh bread mingles with livestock.",
            location_type="town",
            region_id=doromir_lowlands.id,
            danger_modifier=-1,
            wealth_modifier=1,  # Slightly wealthier due to trade
            population_density="crowded",
            accessibility="public"
        )
        manor = Location(
            name="Millhaven Manor",
            description="The stately residence of Baron Aldric, perched on a low hill overlooking the town. Grey stone walls and a modest tower speak of old nobility. Guards patrol the grounds.",
            location_type="manor",
            region_id=doromir_lowlands.id,
            danger_modifier=-2,  # Very safe, heavily guarded
            wealth_modifier=2,  # Wealthier than surroundings
            population_density="sparse",
            accessibility="restricted",
            notes="Seat of regional government. Audiences with the Baron by appointment."
        )
        db.add_all([tavern, forest, market, manor])
        db.flush()
        print(f"  ✓ Created locations: {tavern.name}, {forest.name}, {market.name}, {manor.name}")
        
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
        tavern_keepers = Faction(
            name="Tavern Keepers of Doromir",
            description="A loose association of innkeepers and tavernkeepers who share information about travelers, troublemakers, and trade. They look out for each other and their establishments.",
            alignment=AlignmentType.NEUTRAL
        )
        barons_court = Faction(
            name="Baron's Court of Millhaven",
            description="The formal governing body of the Doromir Lowlands. Includes the Baron, his advisors, the town guard, and appointed officials. They maintain order and collect taxes.",
            alignment=AlignmentType.LAWFUL
        )
        village_folk = Faction(
            name="Villagers of Doromir",
            description="The common folk of the region - farmers, craftsmen, and laborers. They have no formal organization but share a sense of community and mutual aid.",
            alignment=AlignmentType.NEUTRAL
        )
        db.add_all([merchants_guild, tavern_keepers, barons_court, village_folk])
        db.flush()
        print(f"  ✓ Created factions: {merchants_guild.name}, {tavern_keepers.name}, {barons_court.name}, {village_folk.name}")
        
        # === NPCs ===
        innkeeper = NonPlayerCharacter(
            name="Greta Ironbrew",
            npc_type="innkeeper",
            health=40,
            max_health=40,
            behavior_state=BehaviorState.PASSIVE,
            base_disposition=30,
            description="A stout dwarven woman with braided auburn hair and a warm smile. She runs the Rusty Tankard with an iron fist and a generous heart.",
            dialogue="Welcome to the Rusty Tankard, traveler! Sit, drink, and tell me your tale.",
            location_id=tavern.id,
            race_id=dwarf.id,
            faction_id=tavern_keepers.id,
            personality_traits={
                "friendly": True,
                "shrewd": True,
                "protective_of_patrons": True,
                "loves_gossip": True
            }
        )
        
        merchant = NonPlayerCharacter(
            name="Tomas Fairweather",
            npc_type="merchant",
            health=30,
            max_health=30,
            behavior_state=BehaviorState.PASSIVE,
            base_disposition=20,
            description="A lanky human man with a weathered face and quick eyes. His stall at the market is always well-stocked with goods from across the region.",
            dialogue="Fine wares, fair prices! What catches your eye today, friend?",
            location_id=market.id,
            race_id=human.id,
            faction_id=merchants_guild.id,
            personality_traits={
                "opportunistic": True,
                "well_informed": True,
                "haggler": True,
                "honest": True
            }
        )
        
        baron = NonPlayerCharacter(
            name="Baron Aldric of Millhaven",
            npc_type="noble",
            health=50,
            max_health=50,
            behavior_state=BehaviorState.PASSIVE,
            base_disposition=0,  # Neutral to strangers
            description="A distinguished human man in his fifties with silver-streaked hair and a neatly trimmed beard. He wears simple but well-made clothes and carries himself with quiet authority.",
            dialogue="You seek an audience? State your business plainly - I have little patience for flattery.",
            location_id=manor.id,
            race_id=human.id,
            faction_id=barons_court.id,
            personality_traits={
                "just": True,
                "pragmatic": True,
                "weary_of_politics": True,
                "protective_of_people": True,
                "dislikes_sycophants": True
            }
        )
        
        guard_captain = NonPlayerCharacter(
            name="Captain Mira Stoneshield",
            npc_type="guard",
            health=60,
            max_health=60,
            behavior_state=BehaviorState.DEFENSIVE,
            base_disposition=10,
            description="A tall, muscular human woman with short-cropped black hair and a scar across her left cheek. She wears the Baron's livery and a well-used sword.",
            dialogue="Keep your nose clean and we'll have no trouble. Cause problems, and you'll answer to me.",
            location_id=manor.id,
            race_id=human.id,
            faction_id=barons_court.id,
            personality_traits={
                "disciplined": True,
                "loyal": True,
                "suspicious_of_strangers": True,
                "fair_but_firm": True
            }
        )
        
        db.add_all([innkeeper, merchant, baron, guard_captain])
        print(f"  ✓ Created NPCs: {innkeeper.name}, {merchant.name}, {baron.name}, {guard_captain.name}")
        
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
