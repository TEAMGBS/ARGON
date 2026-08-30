"""/link list — show a user's linked accounts."""

import discord

from database.db import get_pool
from utils.embeds import base_embed, error_embed
from utils.emojis import E_CORRECT
from utils.resolver import all_tags_for_user


async def list_(interaction: discord.Interaction, user: discord.User = None):
    await interaction.response.defer(ephemeral=True)
    target = user or interaction.user
    pool = await get_pool()
    rows = await all_tags_for_user(pool, target.id)
    if not rows:
        await interaction.followup.send(embed=error_embed(f"{target.mention} has no linked accounts. Use `/link add`."))
        return

    lines = []
    for i, row in enumerate(rows):
        mark = E_CORRECT if row["verified"] else "•"
        default = " _(default)_" if i == 0 else ""
        lines.append(f"{mark} **{row['name'] or row['tag']}** `{row['tag']}`{default}")

    embed = await base_embed(interaction, title=f"{target.display_name} — Linked Accounts")
    embed.description = "\n".join(lines)
    await interaction.followup.send(embed=embed)
