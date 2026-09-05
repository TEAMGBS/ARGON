"""/setup rmwar-log, delete a war log by its id."""

from __future__ import annotations

import discord

from database import warlogs as warlogs_db
from utils.embeds import error_embed, success_embed


async def handle(interaction: discord.Interaction, warlog_id: str) -> None:
    warlog_id = warlog_id.strip().upper()
    row = await warlogs_db.get_by_id(interaction.guild_id, warlog_id)
    if not row:
        await interaction.response.send_message(
            embed=error_embed(f"No war log with id `{warlog_id}` on this server."), ephemeral=True
        )
        return
    await warlogs_db.remove_by_id(interaction.guild_id, warlog_id)
    await interaction.response.send_message(
        embed=success_embed(f"Removed war log `{warlog_id}` for `{row['tag']}`."), ephemeral=True
    )
