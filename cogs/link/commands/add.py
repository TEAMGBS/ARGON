"""/link add — link a player tag to a Discord user."""

import discord

from database.db import get_pool
from utils.embeds import error_embed, success_embed
from utils.emojis import get_th_emoji
from utils.tags import is_valid_tag, normalize_tag


async def add(interaction: discord.Interaction, tag: str, user: discord.User = None):
    await interaction.response.defer(ephemeral=True)

    if not is_valid_tag(tag):
        await interaction.followup.send(embed=error_embed("That is not a valid player tag."))
        return
    tag = normalize_tag(tag)

    try:
        player = await interaction.client.coc_client.get_player(tag)
    except Exception:
        await interaction.followup.send(embed=error_embed(f"No player found for `{tag}`."))
        return

    target = user or interaction.user
    pool = await get_pool()
    owner = await pool.fetchrow("SELECT discord_id FROM linked_accounts WHERE tag = $1", tag)
    if owner:
        who = "you" if owner["discord_id"] == target.id else "someone else"
        await interaction.followup.send(embed=error_embed(f"`{tag}` is already linked to {who}."))
        return

    await pool.execute(
        "INSERT INTO linked_accounts (discord_id, tag, name) VALUES ($1, $2, $3)",
        target.id,
        tag,
        player.name,
    )
    await interaction.followup.send(
        embed=success_embed(f"Linked {get_th_emoji(player.town_hall)} **{player.name}** (`{tag}`) to {target.mention}.")
    )
