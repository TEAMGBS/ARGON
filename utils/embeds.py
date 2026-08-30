"""Shared embed helpers and colours used across every cog."""

import discord

from database.db import get_pool
from utils.emojis import E_CORRECT, E_WARN, E_WRONG

GREEN = 0x57F287
RED = 0xED4245
YELLOW = 0xFEE75C
BLURPLE = 0x5865F2


def success_embed(message: str) -> discord.Embed:
    return discord.Embed(description=f"{E_CORRECT} {message}", color=GREEN)


def error_embed(message: str) -> discord.Embed:
    return discord.Embed(description=f"{E_WRONG} {message}", color=RED)


def warn_embed(message: str) -> discord.Embed:
    return discord.Embed(description=f"{E_WARN} {message}", color=YELLOW)


async def guild_color(guild_id) -> discord.Color:
    """The embed colour configured for a guild (via /config), else the default."""
    if guild_id is not None:
        try:
            pool = await get_pool()
            row = await pool.fetchrow("SELECT color FROM guild_settings WHERE guild_id = $1", int(guild_id))
            if row and row["color"]:
                return discord.Color(int(row["color"], 16))
        except Exception:
            pass
    return discord.Color(BLURPLE)


async def base_embed(interaction: discord.Interaction, **kwargs) -> discord.Embed:
    """An embed pre-coloured for the current guild."""
    color = await guild_color(interaction.guild_id)
    return discord.Embed(color=color, **kwargs)
