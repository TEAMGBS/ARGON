"""/setup list-war-logs, list the war logs configured on this server."""

from __future__ import annotations

import discord

from cogs.reminders.duration import format_minutes
from database import warlogs as warlogs_db
from utils.embeds import base_embed, error_embed

from ..lookups import WAR_TYPE_LABELS


async def handle(interaction: discord.Interaction) -> None:
    rows = await warlogs_db.list_for_guild(interaction.guild_id)
    if not rows:
        await interaction.response.send_message(
            embed=error_embed("No war logs configured. Set one up with `/setup war-logs`."), ephemeral=True
        )
        return

    embed = await base_embed(interaction, title="War Logs")
    lines = []
    for row in rows:
        name = row["name"] or row["tag"]
        wtype = WAR_TYPE_LABELS.get(row["war_type"], row["war_type"] or "All")
        marks = ", ".join(format_minutes(m) for m in (row["timings"] or []))
        lines.append(f"`{row['id']}` • **{name}** (`{row['tag']}`) • {wtype} • <#{row['channel_id']}> • {marks} left")
    embed.description = "\n".join(lines)[:4000]
    embed.set_footer(text=f"{len(rows)} war log(s)")
    await interaction.response.send_message(embed=embed, ephemeral=True)
