"""Shared helpers for the war-log commands: the id autocomplete and labels."""

from __future__ import annotations

import discord
from discord import app_commands

from database import warlogs as warlogs_db

WAR_TYPE_LABELS = {"normal": "Normal", "cwl": "CWL", "friendly": "Friendly", "": "All"}


async def warlog_autocomplete(interaction: discord.Interaction, current: str) -> list[app_commands.Choice]:
    if not interaction.guild_id:
        return []
    query = (current or "").strip().lower()
    choices = []
    for row in await warlogs_db.list_for_guild(interaction.guild_id):
        name = row["name"] or row["tag"]
        wtype = WAR_TYPE_LABELS.get(row["war_type"], row["war_type"] or "All")
        label = f"{row['id']} · {name} · {wtype}"
        if not query or query in label.lower():
            choices.append(app_commands.Choice(name=label[:100], value=row["id"]))
        if len(choices) >= 25:
            break
    return choices
