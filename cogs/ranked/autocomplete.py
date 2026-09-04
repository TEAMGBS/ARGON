"""Player-tag autocomplete for ranked commands.

Suggests any tag the bot has already seen - tracked players, previously polled
players, and linked accounts - while still accepting a freshly typed tag.
"""

from __future__ import annotations

import discord
from discord import app_commands

from database import ranked as ranked_db


async def tag_autocomplete(interaction: discord.Interaction, current: str) -> list[app_commands.Choice]:
    rows = await ranked_db.known_tags((current or "").strip(), limit=25)
    choices = []
    for row in rows:
        name = row["name"]
        label = f"{name} ({row['tag']})" if name else row["tag"]
        choices.append(app_commands.Choice(name=label[:100], value=row["tag"]))
    return choices
