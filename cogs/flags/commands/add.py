"""/flag add — flag a player for monitoring."""

import discord

from database.db import get_pool
from utils.embeds import error_embed, success_embed
from utils.tags import is_valid_tag, normalize_tag


async def flag_add(interaction: discord.Interaction, tag: str, reason: str):
    await interaction.response.defer()
    if not is_valid_tag(tag):
        await interaction.followup.send(embed=error_embed("Invalid player tag."))
        return
    tag = normalize_tag(tag)

    name = tag
    try:
        player = await interaction.client.coc_client.get_player(tag)
        name = player.name
    except Exception:
        pass

    pool = await get_pool()
    await pool.execute(
        """INSERT INTO flags (guild_id, tag, name, reason, flagged_by) VALUES ($1, $2, $3, $4, $5)
           ON CONFLICT (guild_id, tag) DO UPDATE SET reason = EXCLUDED.reason, name = EXCLUDED.name,
             flagged_by = EXCLUDED.flagged_by""",
        interaction.guild_id,
        tag,
        name,
        reason,
        interaction.user.id,
    )
    await interaction.followup.send(embed=success_embed(f"Flagged **{name}** (`{tag}`)."))
