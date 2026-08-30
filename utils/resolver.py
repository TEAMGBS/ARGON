"""Shared resolution logic: turn command arguments into CoC Player/Clan objects,
plus the linked-account lookups several cogs need.

A player argument can be an explicit tag, a @mentioned user's default account, or
(when omitted) the invoker's own default linked account. A clan argument can be an
explicit tag, a saved alias, or (when omitted) the guild's first linked clan.
"""

import coc
import discord
from discord import app_commands

from database.db import get_pool
from utils.tags import is_valid_tag, normalize_tag


async def default_tag_for_user(pool, discord_id: int):
    """The user's first-linked (default) account tag, or None."""
    row = await pool.fetchrow(
        "SELECT tag FROM linked_accounts WHERE discord_id = $1 ORDER BY linked_at ASC LIMIT 1",
        discord_id,
    )
    return row["tag"] if row else None


async def all_tags_for_user(pool, discord_id: int):
    """All accounts linked by a user, default first."""
    return await pool.fetch(
        "SELECT tag, name, verified, linked_at FROM linked_accounts "
        "WHERE discord_id = $1 ORDER BY linked_at ASC",
        discord_id,
    )


async def resolve_player(interaction: discord.Interaction, tag: str = None, user: discord.User = None):
    """Return a coc.Player, or raise ValueError(message) with a user-facing reason."""
    coc_client = interaction.client.coc_client
    pool = await get_pool()

    if not tag:
        target_id = user.id if user else interaction.user.id
        tag = await default_tag_for_user(pool, target_id)
        if not tag:
            who = user.mention if user else "You"
            verb = "hasn't" if user else "haven't"
            raise ValueError(f"{who} {verb} linked a Clash of Clans account. Use `/link add`.")

    if not is_valid_tag(tag):
        raise ValueError(f"`{tag}` is not a valid player tag.")

    try:
        return await coc_client.get_player(normalize_tag(tag))
    except coc.NotFound:
        raise ValueError(f"No player found for tag `{normalize_tag(tag)}`.")
    except Exception:
        raise ValueError("Clash of Clans API request failed, try again in a bit.")


async def resolve_clan(interaction: discord.Interaction, tag: str = None):
    """Return a coc.Clan, or raise ValueError(message) with a user-facing reason."""
    coc_client = interaction.client.coc_client
    pool = await get_pool()

    # An argument that isn't a tag may be a saved alias for this guild.
    if tag and not is_valid_tag(tag) and interaction.guild_id:
        row = await pool.fetchrow(
            "SELECT tag FROM aliases WHERE guild_id = $1 AND name = $2",
            interaction.guild_id,
            tag.strip().lower(),
        )
        if row:
            tag = row["tag"]

    # No argument: fall back to the guild's first linked clan.
    if not tag and interaction.guild_id:
        row = await pool.fetchrow(
            "SELECT tag FROM clan_stores WHERE guild_id = $1 ORDER BY created_at ASC LIMIT 1",
            interaction.guild_id,
        )
        if row:
            tag = row["tag"]

    if not tag:
        raise ValueError("No clan tag given and no clan is linked to this server. Use `/setup clan`.")
    if not is_valid_tag(tag):
        raise ValueError(f"`{tag}` is not a valid clan tag or alias.")

    try:
        return await coc_client.get_clan(normalize_tag(tag))
    except coc.NotFound:
        raise ValueError(f"No clan found for tag `{normalize_tag(tag)}`.")
    except Exception:
        raise ValueError("Clash of Clans API request failed, try again in a bit.")


async def clan_autocomplete(interaction: discord.Interaction, current: str):
    """Suggest clans linked in the current guild for a clan-tag option."""
    if not interaction.guild_id:
        return []
    pool = await get_pool()
    rows = await pool.fetch("SELECT tag, name FROM clan_stores WHERE guild_id = $1 LIMIT 25", interaction.guild_id)
    query = (current or "").lower()
    choices = []
    for row in rows:
        label = f"{row['name']} ({row['tag']})"
        if not query or query in label.lower():
            choices.append(app_commands.Choice(name=label[:100], value=row["tag"]))
    return choices[:25]
