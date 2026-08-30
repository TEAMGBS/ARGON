"""/flag remove — remove a flag."""

import discord

from database.db import get_pool
from utils.embeds import error_embed, success_embed
from utils.tags import normalize_tag


async def flag_remove(interaction: discord.Interaction, tag: str):
    await interaction.response.defer()
    tag = normalize_tag(tag)
    pool = await get_pool()
    result = await pool.execute("DELETE FROM flags WHERE guild_id = $1 AND tag = $2", interaction.guild_id, tag)
    if result.endswith("0"):
        await interaction.followup.send(embed=error_embed(f"No flag on `{tag}`."))
        return
    await interaction.followup.send(embed=success_embed(f"Removed flag on `{tag}`."))
