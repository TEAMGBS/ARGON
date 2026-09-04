"""/ranked list, show the players this server is tracking."""

from __future__ import annotations

import discord

from database import ranked as ranked_db
from utils.embeds import base_embed, error_embed

from ._guard import require_manage


async def handle(interaction: discord.Interaction) -> None:
    if not await require_manage(interaction):
        return
    rows = await ranked_db.get_tracked_for_guild(interaction.guild_id)
    if not rows:
        await interaction.response.send_message(
            embed=error_embed("No players are being tracked. Add one with `/ranked track-player`."), ephemeral=True
        )
        return

    channel_id = await ranked_db.get_channel(interaction.guild_id)
    embed = await base_embed(interaction, title="Tracked Legend Players")
    lines = [f"**{row['name']}** (`{row['tag']}`)" for row in rows]
    if channel_id:
        lines.append(f"\nNotifications: <#{channel_id}>")
    else:
        lines.append("\n_No notification channel set. Use `/ranked track-setup`._")
    embed.description = "\n".join(lines)[:4000]
    embed.set_footer(text=f"{len(rows)} player(s)")
    await interaction.response.send_message(embed=embed, ephemeral=True)
