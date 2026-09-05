"""Custom emoji registry for the bot.

CUSTOM holds every application emoji uploaded to the bot, keyed by its emoji
name exactly as shown by /emoji show. The lookup helpers match Clash of Clans
league, unit and Town Hall names to these, so command output shows real game
icons.

Emojis are being re-added to the bot, so this file currently holds only the CWL
war-league icons. Paste more batches from /emoji show and add them to CUSTOM;
the helpers and semantic constants below already fall back to plain unicode when
a name is missing, so a partial registry never breaks a command.

Note: Discord does not render custom emojis inside `code` spans or code blocks,
so callers must place these strings outside backticks.
"""

import re

# Every application emoji the bot owns (from /emoji show).
CUSTOM = {
    "cwlbronze1": "<:cwlbronze1:1545082659791966249>",
    "cwlbronze2": "<:cwlbronze2:1545082663998857247>",
    "cwlbronze3": "<:cwlbronze3:1545082665273663600>",
    "cwlchamp1": "<:cwlchamp1:1545077517424001095>",
    "cwlchamp2": "<:cwlchamp2:1545077519429013554>",
    "cwlchamp3": "<:cwlchamp3:1545077521295605810>",
    "cwlcrystal1": "<:cwlcrystal1:1545077530766217288>",
    "cwlcrystal2": "<:cwlcrystal2:1545077532393603085>",
    "cwlcrystal3": "<:cwlcrystal3:1545077535090417704>",
    "cwlgold1": "<:cwlgold1:1545082666351722577>",
    "cwlgold2": "<:cwlgold2:1545082667396239480>",
    "cwlgold3": "<:cwlgold3:1545082668226580561>",
    "cwllegend": "<:cwllegend:1545077509580791869>",
    "cwlmaster1": "<:cwlmaster1:1545077522889318481>",
    "cwlmaster2": "<:cwlmaster2:1545077525573533719>",
    "cwlmaster3": "<:cwlmaster3:1545077528660672662>",
    "cwlsilver1": "<:cwlsilver1:1545082669619216475>",
    "cwlsilver2": "<:cwlsilver2:1545082671284224020>",
    "cwlsilver3": "<:cwlsilver3:1545082672227946548>",
    "cwltitan1": "<:cwltitan1:1545077511535198239>",
    "cwltitan2": "<:cwltitan2:1545077513301008518>",
    "cwltitan3": "<:cwltitan3:1545077515280846938>",
    "Unranked": "<:Unranked:1545082673561608283>",
    "TH2": "<:TH2:1545090379697627166>",
    "TH3": "<:TH3:1545090381501300756>",
    "TH4": "<:TH4:1545090383837397122>",
    "TH5": "<:TH5:1545090386303647764>",
    "TH6": "<:TH6:1545090388178640936>",
    "TH7": "<:TH7:1545090389839716415>",
    "TH8": "<:TH8:1545090391852843088>",
    "TH9": "<:TH9:1545090393639489687>",
    "TH10": "<:TH10:1545090395262689302>",
    "TH11": "<:TH11:1545090401655066792>",
    "TH12": "<:TH12:1545090404305608804>",
    "TH13": "<:TH13:1545090405719089163>",
    "TH14": "<:TH14:1545090408680521859>",
    "TH15": "<:TH15:1545090410412511302>",
    "TH16": "<:TH16:1545090411863736495>",
    "TH17": "<:TH17:1545090414770528286>",
    "TH18": "<:TH18:1545090419447173201>",
    "emptystar": "<:emptystar:1545759771267956747>",
    "shield": "<:shield:1545760486610440322>",
    "star": "<:star:1545767567237324810>",
    "sword": "<:sword:1545760484500840459>",
    "vs": "<:vs:1545760485595684904>",
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


# Clash of Clans war-league tiers (in-game name -> the family used in our emoji
# registry). CWL war leagues are named like "Champion League I", "Crystal League
# III", etc. We map the tier word to an emoji family and the trailing roman
# numeral to 1/2/3.
_CWL_TIER_FAMILY = {
    "champion": "cwlchamp",
    "titan": "cwltitan",
    "master": "cwlmaster",
    "crystal": "cwlcrystal",
    "gold": "cwlgold",
    "silver": "cwlsilver",
    "bronze": "cwlbronze",
}

_ROMAN = {"i": 1, "ii": 2, "iii": 3}


def cwl_league_emoji(name: str, default: str = "") -> str:
    """Emoji for a clan's CWL war league by its in-game name, e.g.
    "Champion League I" -> <:cwlchamp1:...>. Returns the Legend or Unranked
    icon for those leagues, and ``default`` when there is no match."""
    if not name:
        return default
    lowered = name.lower()
    if "legend" in lowered:
        return CUSTOM.get("cwllegend", default)
    if "unranked" in lowered:
        return CUSTOM.get("Unranked", default)

    family = next((fam for word, fam in _CWL_TIER_FAMILY.items() if word in lowered), None)
    if not family:
        return default

    # Trailing roman numeral -> tier number (defaults to 1 when absent).
    token = lowered.replace("league", "").strip().split()
    tier = _ROMAN.get(token[-1], 1) if token else 1
    return CUSTOM.get(f"{family}{tier}", default)


# ── Semantic constants used across cogs ───────────────────────────────────────
# Real custom emojis where one exists, unicode fallbacks otherwise. The .get
# fallbacks keep these working while the non-league emojis are being re-added.
E_PEOPLE = CUSTOM.get("people", "👥")
E_UP = CUSTOM.get("up_green_arrow", "🟢")
E_DOWN = CUSTOM.get("down_red_arrow", "🔴")
E_HERO = CUSTOM.get("BarbarianKing", "👑")
E_TROOP = CUSTOM.get("barbarian", "⚔️")
E_SPELL = CUSTOM.get("Lightning", "⚡")
E_VERSUS_TROPHY = CUSTOM.get("versus_trophy", "🏅")

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

# War-log icons (custom where uploaded, unicode fallback otherwise).
E_SWORD_ICON = CUSTOM.get("sword", "🗡️")
E_SHIELD_ICON = CUSTOM.get("shield", "🛡️")
E_VS = CUSTOM.get("vs", "vs")
E_STAR_FULL = CUSTOM.get("star", "⭐")
E_STAR_EMPTY = CUSTOM.get("emptystar", "☆")


def war_stars(count: int) -> str:
    """A three-slot star row for a war attack or result, using the custom star
    emojis (filled + empty), e.g. 2 stars -> star star emptystar."""
    count = max(0, min(3, count or 0))
    return E_STAR_FULL * count + E_STAR_EMPTY * (3 - count)
