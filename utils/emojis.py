"""Emoji glyphs used across the bot.

These are plain unicode placeholders so the bot works out of the box. To get the
polished ClashPerk look, upload custom emojis to a server the bot is in and swap
the values below for their ``<:name:id>`` strings (same interface — the cogs call
``get_th_emoji`` etc., so only this file changes).
"""

# Status / info
E_CORRECT = "✅"
E_WRONG = "❌"
E_WARN = "⚠️"
E_INFO = "ℹ️"

# Clash of Clans
E_CLAN = "🛡️"
E_TROPHY = "🏆"
E_STAR = "⭐"
E_SWORD = "🗡️"
E_SHIELD = "🛡️"
E_FIRE = "🔥"
E_CLOCK = "⏱️"
E_PEOPLE = "👥"
E_XP = "✨"
E_TOWNHALL = "🏛️"
E_DONATE = "📤"
E_RECEIVE = "📥"
E_HERO = "🦸"
E_TROOP = "🪖"
E_SPELL = "🧪"
E_UP = "⬆️"
E_DOWN = "⬇️"
E_PERCENT = "💥"


def get_th_emoji(th_level) -> str:
    """Town Hall glyph. Replace with custom TH emojis for the full look."""
    return f"{E_TOWNHALL}TH{th_level}"


def war_stars(count: int) -> str:
    """A three-slot star row for a war attack/result."""
    count = max(0, min(3, count or 0))
    return "⭐" * count + "☆" * (3 - count)
