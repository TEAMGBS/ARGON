"""/ranked track-setup, set the channel legend notifications are posted to."""

from __future__ import annotations

import discord

from database import ranked as ranked_db
from utils.embeds import success_embed

from ._guard import require_manage


async def handle(interaction: discord.Interaction, channel: discord.TextChannel) -> None:
    if not await require_manage(interaction):
        return
    await ranked_db.set_channel(interaction.guild_id, channel.id)
    await interaction.response.send_message(
        embed=success_embed(f"Legend attack/defense notifications will be posted in {channel.mention}."),
        ephemeral=True,
    )
