"""Custom emoji registry for the bot.

CUSTOM holds every application emoji uploaded to the bot, keyed by its emoji
name exactly as shown by /emoji show. The lookup helpers match Clash of Clans
unit and Town Hall names to these, so command output shows real game icons.

Note: Discord does not render custom emojis inside `code` spans or code blocks,
so callers must place these strings outside backticks.
"""

import re

# Every application emoji the bot owns (from /emoji show).
CUSTOM = {
    "ActionFigure": "<:ActionFigure:1538885126153441430>",
    "AngryJelly": "<:AngryJelly:1538881881569890364>",
    "ApprenticeWarden": "<:ApprenticeWarden:1538882586158301185>",
    "archer": "<:archer:1538872678356615228>",
    "ArcherLeague": "<:ArcherLeague:1538898264697348118>",
    "ArcherPuppet": "<:ArcherPuppet:1538886117418598531>",
    "ArcherQueen": "<:ArcherQueen:1538876524307021824>",
    "babydragon": "<:babydragon:1538876343457030214>",
    "balloon": "<:balloon:1538875681050595382>",
    "barbarian": "<:barbarian:1538872578045911170>",
    "BarbarianKing": "<:BarbarianKing:1538876339015393310>",
    "BarbarianLeague": "<:BarbarianLeague:1538898246385147985>",
    "BarbarianPuppet": "<:BarbarianPuppet:1538886105481347165>",
    "Bat": "<:Bat:1538885365107138610>",
    "BattleBlimp": "<:BattleBlimp:1538885398938263582>",
    "BattleDrill": "<:BattleDrill:1538885427769905202>",
    "BattleMachine": "<:BattleMachine:1538887530857103441>",
    "BC": "<:BC:1538887536884060292>",
    "BetaMinion": "<:BetaMinion:1538882283639930970>",
    "blank": "<:blank:1538896623612989490>",
    "Bomber": "<:Bomber:1538883003244216350>",
    "bowler": "<:bowler:1538882335813013596>",
    "BoxerGiant": "<:BoxerGiant:1538882190740426804>",
    "CannonCart": "<:CannonCart:1538882367840722964>",
    "Clone": "<:Clone:1538883622709497856>",
    "cwlchamp1": "<:cwlchamp1:1538887771047989278>",
    "cwlchamp2": "<:cwlchamp2:1538887776689332308>",
    "cwlchamp3": "<:cwlchamp3:1538887782536187995>",
    "cwlcrystal1": "<:cwlcrystal1:1538887787925999666>",
    "cwlcrystal2": "<:cwlcrystal2:1538887793382658169>",
    "cwlcrystal3": "<:cwlcrystal3:1538887799376183387>",
    "cwllegend": "<:cwllegend:1538879392107995206>",
    "cwlmaster1": "<:cwlmaster1:1538887804736503899>",
    "cwlmaster2": "<:cwlmaster2:1538887810596077599>",
    "cwlmaster3": "<:cwlmaster3:1538887816988205188>",
    "cwltitan1": "<:cwltitan1:1538887823044907098>",
    "cwltitan2": "<:cwltitan2:1538887829462188094>",
    "cwltitan3": "<:cwltitan3:1538887835807912086>",
    "DarkOrb": "<:DarkOrb:1538884796250333274>",
    "Diggy": "<:Diggy:1538881677722521620>",
    "down_red_arrow": "<:down_red_arrow:1538896634912710706>",
    "dragon": "<:dragon:1538876064455991438>",
    "DragonDuke": "<:DragonDuke:1538876758244458618>",
    "DragonLeague": "<:DragonLeague:1538898258284253396>",
    "dragonrider": "<:dragonrider:1538876527503081492>",
    "DropShip": "<:DropShip:1538882576268140625>",
    "Druid": "<:Druid:1538882691116830822>",
    "earth": "<:earth:1538896612762320947>",
    "Earthquake": "<:Earthquake:1538885148710539349>",
    "EarthquakeBoots": "<:EarthquakeBoots:1538886152264745042>",
    "ElectroBoots": "<:ElectroBoots:1538884153963978823>",
    "electrodragon": "<:electrodragon:1538876453901312080>",
    "ElectroFangs": "<:ElectroFangs:1538885629650411660>",
    "ElectroLeague": "<:ElectroLeague:1538898252601106432>",
    "electrotitan": "<:electrotitan:1538876567621468290>",
    "EternalTome": "<:EternalTome:1538886129544208384>",
    "EW": "<:EW:1538882803066736670>",
    "Fireball": "<:Fireball:1538886217763004497>",
    "FireHeart": "<:FireHeart:1538885382714953750>",
    "FlameBlower": "<:FlameBlower:1538885572712734781>",
    "FlameFlinger": "<:FlameFlinger:1538885421944152235>",
    "Freeze": "<:Freeze:1538883496460689408>",
    "FrostFlake": "<:FrostFlake:1538885276460388363>",
    "Frosty": "<:Frosty:1538881750669983794>",
    "FrozenArrow": "<:FrozenArrow:1538886194774147102>",
    "Furnace": "<:Furnace:1538882763430567986>",
    "giant": "<:giant:1538872716260544532>",
    "GiantArrow": "<:GiantArrow:1538886200490991728>",
    "GiantGauntlet": "<:GiantGauntlet:1538886164180897883>",
    "goblin": "<:goblin:1538873009526280234>",
    "Golem": "<:Golem:1538881998645497937>",
    "GolemLeague": "<:GolemLeague:1538898240387162234>",
    "GrandWarden": "<:GrandWarden:1538876568703733760>",
    "GreedyRaven": "<:GreedyRaven:1538882017008291980>",
    "Haste": "<:Haste:1538885235012276274>",
    "HasteVial": "<:HasteVial:1538886176302174303>",
    "Headhunter": "<:Headhunter:1538882509314588722>",
    "healer": "<:healer:1538875859463577670>",
    "HealerPuppet": "<:HealerPuppet:1538886211945365605>",
    "Healing": "<:Healing:1538883199403425812>",
    "HealingTome": "<:HealingTome:1538883661292642388>",
    "Henchmen": "<:Henchmen:1538884654256492554>",
    "HeroicTorch": "<:HeroicTorch:1538886205779746860>",
    "HogGlider": "<:HogGlider:1538882736062730240>",
    "HogGlider_1": "<:HogGlider_1:1543579645407006830>",
    "HogPuppet": "<:HogPuppet:1538886158459871343>",
    "HogRider": "<:HogRider:1538881693400956981>",
    "IceBlock": "<:IceBlock:1538885694456463481>",
    "IceGolem": "<:IceGolem:1538882436359004231>",
    "IceHound": "<:IceHound:1538887293622820895>",
    "InvisibilityVial": "<:InvisibilityVial:1538886123051417631>",
    "Invisible": "<:Invisible:1538884010632020123>",
    "Jump": "<:Jump:1538883400847462402>",
    "LASSI": "<:LASSI:1538881263371550901>",
    "LavaHound": "<:LavaHound:1538882262723076096>",
    "LavaloonPuppet": "<:LavaloonPuppet:1538884532521140346>",
    "LegendLeague": "<:LegendLeague:1538898234028859494>",
    "LifeGem": "<:LifeGem:1538886135239933972>",
    "Lightning": "<:Lightning:1538883113747353723>",
    "LogLauncher": "<:LogLauncher:1538885416231370843>",
    "MagicMirror": "<:MagicMirror:1538883784978468996>",
    "MetalPants": "<:MetalPants:1538884934251315262>",
    "MeteorGolem": "<:MeteorGolem:1538881262045892709>",
    "MeteorStaff": "<:MeteorStaff:1538885189327917106>",
    "miner": "<:miner:1538876405407027200>",
    "Minion": "<:Minion:1538881499204554752>",
    "MinionPrince": "<:MinionPrince:1538876734626205758>",
    "NightWitch": "<:NightWitch:1538882457414144040>",
    "NobleIron": "<:NobleIron:1538885049712255008>",
    "Overgrowth": "<:Overgrowth:1538885612793237626>",
    "Owl": "<:Owl:1538881406728671324>",
    "pekka": "<:pekka:1538876279749873684>",
    "PekkaLeague": "<:PekkaLeague:1538898228026802236>",
    "people": "<:people:1538896618084896889>",
    "Phoenix": "<:Phoenix:1538881553193504852>",
    "Poison": "<:Poison:1538885070201556992>",
    "PoisonLizard": "<:PoisonLizard:1538881611926609991>",
    "Rage": "<:Rage:1538883293745909820>",
    "RagedBarbarian": "<:RagedBarbarian:1538881978990858361>",
    "RagedBarbarian_1": "<:RagedBarbarian_1:1543579642873647114>",
    "RageGem": "<:RageGem:1538883405305872486>",
    "RageVial": "<:RageVial:1538886111412228197>",
    "rankedlegend": "<:rankedlegend:1538892767239999608>",
    "Recall": "<:Recall:1538884677719302244>",
    "Revive": "<:Revive:1538884760146018436>",
    "RocketBackpack": "<:RocketBackpack:1538883470372245594>",
    "RocketSpear": "<:RocketSpear:1538886182786826312>",
    "RootRider": "<:RootRider:1538880976451534888>",
    "RoyalChampion": "<:RoyalChampion:1538876643114745887>",
    "RoyalGem": "<:RoyalGem:1538886146912686171>",
    "SeekingShield": "<:SeekingShield:1538886140822683682>",
    "SiegeBarracks": "<:SiegeBarracks:1538885410502090772>",
    "SkeletoLeague": "<:SkeletoLeague:1538898221873631242>",
    "Skeleton": "<:Skeleton:1538885298413506651>",
    "SkyWagon": "<:SkyWagon:1538885439195320423>",
    "SnakeBracelet": "<:SnakeBracelet:1538883567252283464>",
    "SneakyArcher": "<:SneakyArcher:1538882105054986240>",
    "Sneezy": "<:Sneezy:1538881935135219742>",
    "SpikeyBall": "<:SpikeyBall:1538886189027954799>",
    "SpiritFox": "<:SpiritFox:1538881806638653540>",
    "StoneSlammer": "<:StoneSlammer:1538885404344848417>",
    "StunBlaster": "<:StunBlaster:1538885472363880478>",
    "SuperPEKKA": "<:SuperPEKKA:1538882654508814478>",
    "TH10": "<:TH10:1538889541161713724>",
    "TH11": "<:TH11:1538889546874232836>",
    "TH12": "<:TH12:1538889553211953182>",
    "TH13": "<:TH13:1538889559369318410>",
    "TH14": "<:TH14:1538889565060857979>",
    "TH15": "<:TH15:1538889571264110714>",
    "TH16": "<:TH16:1538889577509560340>",
    "TH17": "<:TH17:1538889583528255560>",
    "TH18": "<:TH18:1538889589819834398>",
    "TH2": "<:TH2:1538889492612776146>",
    "TH3": "<:TH3:1538889498698580100>",
    "TH4": "<:TH4:1538889504579133580>",
    "TH5": "<:TH5:1538889510455222392>",
    "TH6": "<:TH6:1538889516394356768>",
    "TH7": "<:TH7:1538889522446733428>",
    "TH8": "<:TH8:1538889528746577960>",
    "TH9": "<:TH9:1538889535000158219>",
    "Thrower": "<:Thrower:1538881131011772536>",
    "TitanLeague": "<:TitanLeague:1538898215754006630>",
    "Totem": "<:Totem:1538884838130458684>",
    "TroopLauncher": "<:TroopLauncher:1538885433167974553>",
    "Unicorn": "<:Unicorn:1538881471077417010>",
    "up_green_arrow": "<:up_green_arrow:1538896629199933571>",
    "ValkariyeLeague": "<:ValkariyeLeague:1538898197144150066>",
    "valkyrie": "<:valkyrie:1538881880680701982>",
    "Vampstache": "<:Vampstache:1538886170463969360>",
    "versus_trophy": "<:versus_trophy:1538896607314055229>",
    "wallbreaker": "<:wallbreaker:1538872778357346425>",
    "WallWrecker": "<:WallWrecker:1538885392810385410>",
    "Witch": "<:Witch:1538882130526871583>",
    "WitchLeague": "<:WitchLeague:1538898209621942324>",
    "wizard": "<:wizard:1538875716714762320>",
    "WizardLeague": "<:WizardLeague:1538898203041071155>",
    "Yak": "<:Yak:1538881344149655657>",
    "yeti": "<:yeti:1538876488139546734>",
}


def _norm(name: str) -> str:
    """Lowercase and strip everything but letters and digits, for fuzzy matching."""
    return re.sub(r"[^a-z0-9]", "", (name or "").lower())


# Index every custom emoji by its normalized name for name-based lookups.
_BY_NORM = {_norm(key): value for key, value in CUSTOM.items()}


def emoji(name: str, default: str = "") -> str:
    """Return the custom emoji whose name matches (fuzzily), else `default`."""
    return _BY_NORM.get(_norm(name), default)


def get_unit_emoji(name: str) -> str:
    """Emoji for a Clash of Clans troop, hero, spell or pet by its in-game name.

    Falls back to a spell name without the trailing 'Spell' (the spell emojis are
    named 'Lightning', 'Healing', etc.). Returns "" when there is no match.
    """
    n = _norm(name)
    if n in _BY_NORM:
        return _BY_NORM[n]
    if n.endswith("spell"):
        stripped = n[: -len("spell")]
        if stripped in _BY_NORM:
            return _BY_NORM[stripped]
    return ""


def get_th_emoji(level) -> str:
    """Town Hall emoji for a level, e.g. 15 -> <:TH15:...>. Falls back to text."""
    return CUSTOM.get(f"TH{level}", f"TH{level}")


# ── Semantic constants used across cogs ───────────────────────────────────────
# Real custom emojis where one exists, unicode fallbacks otherwise.
E_PEOPLE = CUSTOM["people"]
E_UP = CUSTOM["up_green_arrow"]
E_DOWN = CUSTOM["down_red_arrow"]
E_HERO = CUSTOM["BarbarianKing"]
E_TROOP = CUSTOM["barbarian"]
E_SPELL = CUSTOM["Lightning"]
E_VERSUS_TROPHY = CUSTOM["versus_trophy"]

E_CLAN = "🛡️"
E_TROPHY = "🏆"
E_STAR = "⭐"
E_SWORD = "🗡️"
E_SHIELD = "🛡️"
E_FIRE = "🔥"
E_CLOCK = "⏱️"
E_XP = "✨"
E_TOWNHALL = "🏛️"
E_DONATE = "📤"
E_RECEIVE = "📥"
E_PERCENT = "💥"

E_CORRECT = "✅"
E_WRONG = "❌"
E_WARN = "⚠️"
E_INFO = "ℹ️"


def war_stars(count: int) -> str:
    """A three-slot star row for a war attack or result."""
    count = max(0, min(3, count or 0))
    return "⭐" * count + "☆" * (3 - count)
