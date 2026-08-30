"""/setup log — enable a member/donation/feed log for a clan in a channel."""

import discord

from database.db import get_pool
from utils.embeds import error_embed, success_embed
from utils.tags import normalize_tag


async def log(interaction: discord.Interaction, tag: str, log_type: str, channel: discord.TextChannel):
    await interaction.response.defer()
    tag = normalize_tag(tag)
    pool = await get_pool()

    store = await pool.fetchrow("SELECT name FROM clan_stores WHERE guild_id = $1 AND tag = $2", interaction.guild_id, tag)
    if not store:
        await interaction.followup.send(embed=error_embed(f"`{tag}` is not linked. Add it with `/setup clan` first."))
        return

    await pool.execute(
        """INSERT INTO clan_logs (guild_id, tag, log_type, channel_id) VALUES ($1, $2, $3, $4)
           ON CONFLICT (guild_id, tag, log_type) DO UPDATE SET channel_id = EXCLUDED.channel_id""",
        interaction.guild_id,
        tag,
        log_type,
        channel.id,
    )
    await interaction.followup.send(
        embed=success_embed(f"`{log_type}` log for **{store['name']}** → {channel.mention}.")
    )
