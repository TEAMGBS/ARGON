"""/ranked untrack-player, stop tracking a player in this server."""

from __future__ import annotations

import discord

from database import ranked as ranked_db
from utils.embeds import error_embed, format_tag, success_embed

from ._guard import require_manage


async def handle(interaction: discord.Interaction, tag: str) -> None:
    if not await require_manage(interaction):
        return
    tag = format_tag(tag)
    removed = await ranked_db.remove_tracked(interaction.guild_id, tag)
    if not removed:
        await interaction.response.send_message(
            embed=error_embed(f"`{tag}` is not being tracked in this server."), ephemeral=True
        )
        return
    await interaction.response.send_message(
        embed=success_embed(f"Stopped tracking `{tag}` in this server."), ephemeral=True
    )
