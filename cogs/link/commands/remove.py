"""/link remove, unlink a player tag."""

import discord

from database.db import get_pool
from utils.embeds import error_embed, success_embed
from utils.tags import normalize_tag


async def remove(interaction: discord.Interaction, tag: str):
    await interaction.response.defer(ephemeral=True)
    tag = normalize_tag(tag)
    pool = await get_pool()
    result = await pool.execute(
        "DELETE FROM linked_accounts WHERE discord_id = $1 AND tag = $2",
        interaction.user.id,
        tag,
    )
    # asyncpg returns e.g. "DELETE 1"; the trailing count is 0 when nothing matched.
    if result.endswith("0"):
        await interaction.followup.send(embed=error_embed(f"`{tag}` is not linked to you."))
        return
    await interaction.followup.send(embed=success_embed(f"Unlinked `{tag}`."))
