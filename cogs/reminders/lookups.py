"""Shared autocomplete for picking an existing reminder by its id."""

from __future__ import annotations

import discord
from discord import app_commands

from database import reminders as reminders_db

from .constants import TYPE_LABELS
from .duration import format_minutes


async def reminder_autocomplete(interaction: discord.Interaction, current: str) -> list[app_commands.Choice]:
    """Suggest this guild's reminders (id, type, clan, times) for a reminder_id option."""
    if not interaction.guild_id:
        return []
    rows = await reminders_db.get_reminders_for_guild(interaction.guild_id)
    query = (current or "").strip().lower()
    choices: list[app_commands.Choice] = []
    for row in rows:
        times = ", ".join(format_minutes(m) for m in (row["timing_minutes"] or [])) or "no times"
        label = f"{row['id']} · {TYPE_LABELS.get(row['type'], row['type'])} · {row['clan_tag']} · {times}"
        if not query or query in label.lower():
            choices.append(app_commands.Choice(name=label[:100], value=row["id"]))
        if len(choices) >= 25:
            break
    return choices
