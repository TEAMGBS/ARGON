"""/reminders remove, delete a reminder by its list number."""

import discord

from database.db import get_pool
from utils.embeds import error_embed, success_embed


async def reminder_remove(interaction: discord.Interaction, index: int):
    await interaction.response.defer()
    pool = await get_pool()
    rows = await pool.fetch("SELECT id FROM reminders WHERE guild_id = $1 ORDER BY id", interaction.guild_id)
    if index < 1 or index > len(rows):
        await interaction.followup.send(embed=error_embed("No reminder with that number."))
        return
    await pool.execute("DELETE FROM reminders WHERE id = $1", rows[index - 1]["id"])
    await interaction.followup.send(embed=success_embed(f"Deleted reminder #{index}."))
