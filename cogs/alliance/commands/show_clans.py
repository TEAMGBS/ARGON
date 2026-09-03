"""/alliance show-clans, list the clans added to this server."""

from __future__ import annotations

import discord

from database import clans as clans_db
from utils.embeds import base_embed, error_embed
from utils.emojis import E_CLAN


async def handle(interaction: discord.Interaction) -> None:
    await interaction.response.defer()
    rows = await clans_db.get_clans_for_guild(interaction.guild_id)
    if not rows:
        await interaction.followup.send(embed=error_embed("No clans added yet. Use `/alliance add-clan`."))
        return

    lines = [f"{E_CLAN} **{row['name']}** (`{row['tag']}`)" for row in rows]
    embed = await base_embed(interaction, title="Alliance Clans")
    embed.description = "\n".join(lines)[:4000]
    embed.set_footer(text=f"{len(rows)} clan(s)")
    await interaction.followup.send(embed=embed)
