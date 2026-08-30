"""/reminders add — create a war reminder."""

import discord

from database.db import get_pool
from utils.embeds import error_embed, success_embed
from utils.tags import is_valid_tag, normalize_tag


async def reminder_add(
    interaction: discord.Interaction,
    before: int,
    tag: str,
    channel: discord.TextChannel,
    message: str = None,
    min_remaining: int = 1,
    role: discord.Role = None,
):
    await interaction.response.defer()
    if not is_valid_tag(tag):
        await interaction.followup.send(embed=error_embed("Invalid clan tag."))
        return
    tag = normalize_tag(tag)

    pool = await get_pool()
    await pool.execute(
        """INSERT INTO reminders (guild_id, channel_id, tag, minutes_before, min_remaining, message, role_id)
           VALUES ($1, $2, $3, $4, $5, $6, $7)""",
        interaction.guild_id,
        channel.id,
        tag,
        before,
        min_remaining,
        message or "You still have war attacks remaining!",
        role.id if role else None,
    )
    await interaction.followup.send(
        embed=success_embed(f"War reminder created: **{before} min** before war end for `{tag}` in {channel.mention}.")
    )
