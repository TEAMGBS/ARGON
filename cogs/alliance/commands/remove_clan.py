"""/alliance remove-clan, remove a clan and everything configured for it."""

from __future__ import annotations

import discord

from database import clans as clans_db
from utils.embeds import error_embed, format_tag, success_embed


async def handle(interaction: discord.Interaction, tag: str) -> None:
    await interaction.response.defer()
    tag = format_tag(tag)

    removed = await clans_db.remove_clan(interaction.guild_id, tag)
    if not removed:
        await interaction.followup.send(embed=error_embed(f"`{tag}` is not added to this server."))
        return

    await interaction.followup.send(
        embed=success_embed(f"Removed `{tag}` and any logs and reminders configured for it.")
    )
