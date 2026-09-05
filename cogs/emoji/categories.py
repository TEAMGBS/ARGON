"""Emoji category helpers: normalization and the autocomplete."""

from __future__ import annotations

import discord
from discord import app_commands

from database import emojis as emojis_db

UNCATEGORIZED = "Uncategorized"

# Suggested categories offered alongside whatever the bot has already used.
DEFAULT_CATEGORIES = [
    "CWL",
    "Town Halls",
    "Troops",
    "Heroes",
    "Spells",
    "Pets",
    "Leagues",
    "Capital",
    "Other",
]


def normalize_category(raw: str | None) -> str:
    """Trim and collapse whitespace; empty stays empty (caller decides default)."""
    return " ".join((raw or "").split())


async def category_autocomplete(interaction: discord.Interaction, current: str) -> list[app_commands.Choice]:
    """Suggest the default categories plus any already in use; free text still allowed."""
    known: list[str] = list(DEFAULT_CATEGORIES)
    try:
        for existing in await emojis_db.categories():
            if existing not in known:
                known.append(existing)
    except Exception:
        pass

    query = normalize_category(current)
    if query and query not in known:
        known.insert(0, query)

    lowered = query.lower()
    choices = [c for c in known if not lowered or lowered in c.lower()]
    return [app_commands.Choice(name=c, value=c) for c in choices[:25]]
