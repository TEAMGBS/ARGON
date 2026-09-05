"""/setup remove-war-logs, delete a war log by its id."""

from __future__ import annotations

import discord
from discord import app_commands

from database import warlogs as warlogs_db
from utils.embeds import error_embed, success_embed

_WAR_TYPE_LABELS = {"normal": "Normal", "cwl": "CWL", "friendly": "Friendly", "": "All"}


async def handle(interaction: discord.Interaction, log_id: str) -> None:
    log_id = log_id.strip().upper()
    row = await warlogs_db.get_by_id(interaction.guild_id, log_id)
    if not row:
        await interaction.response.send_message(
            embed=error_embed(f"No war log with id `{log_id}` on this server."), ephemeral=True
        )
        return
    await warlogs_db.remove_by_id(interaction.guild_id, log_id)
    await interaction.response.send_message(
        embed=success_embed(f"Removed war log `{log_id}` for `{row['tag']}`."), ephemeral=True
    )


async def autocomplete(interaction: discord.Interaction, current: str) -> list[app_commands.Choice]:
    if not interaction.guild_id:
        return []
    query = (current or "").strip().lower()
    choices = []
    for row in await warlogs_db.list_for_guild(interaction.guild_id):
        name = row["name"] or row["tag"]
        wtype = _WAR_TYPE_LABELS.get(row["war_type"], row["war_type"] or "All")
        label = f"{row['id']} · {name} · {wtype}"
        if not query or query in label.lower():
            choices.append(app_commands.Choice(name=label[:100], value=row["id"]))
        if len(choices) >= 25:
            break
    return choices
