"""/flag list, list flagged players."""

import discord

from database.db import get_pool
from utils.embeds import base_embed, error_embed
from utils.emojis import E_WRONG


async def flag_list(interaction: discord.Interaction):
    await interaction.response.defer()
    pool = await get_pool()
    rows = await pool.fetch(
        "SELECT tag, name, reason, flagged_by FROM flags WHERE guild_id = $1 ORDER BY created_at DESC",
        interaction.guild_id,
    )
    if not rows:
        await interaction.followup.send(embed=error_embed("No flagged players."))
        return

    embed = await base_embed(interaction, title="Flagged Players")
    embed.description = "\n".join(
        f"{E_WRONG} **{r['name'] or r['tag']}** `{r['tag']}`, {r['reason']} (by <@{r['flagged_by']}>)" for r in rows
    )[:4000]
    await interaction.followup.send(embed=embed)
