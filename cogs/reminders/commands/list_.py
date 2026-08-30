"""/reminders list, list war reminders."""

import discord

from database.db import get_pool
from utils.embeds import base_embed, error_embed


async def reminder_list(interaction: discord.Interaction):
    await interaction.response.defer()
    pool = await get_pool()
    rows = await pool.fetch(
        "SELECT id, tag, channel_id, minutes_before, role_id FROM reminders WHERE guild_id = $1 ORDER BY id",
        interaction.guild_id,
    )
    if not rows:
        await interaction.followup.send(embed=error_embed("No reminders configured. Create one with `/reminders add`."))
        return

    lines = []
    for i, r in enumerate(rows, start=1):
        role = f" • <@&{r['role_id']}>" if r["role_id"] else ""
        lines.append(f"**{i}.** {r['minutes_before']}m before • `{r['tag']}` → <#{r['channel_id']}>{role}")

    embed = await base_embed(interaction, title="War Reminders")
    embed.description = "\n".join(lines)[:4000]
    await interaction.followup.send(embed=embed)
