"""/clan donations, current-season donation leaderboard."""

import discord

from utils.embeds import base_embed, error_embed
from utils.emojis import E_DONATE, E_RECEIVE
from utils.helpers import pad, pad_start
from utils.resolver import resolve_clan


async def donations(interaction: discord.Interaction, tag: str = None):
    await interaction.response.defer()
    try:
        clan = await resolve_clan(interaction, tag)
    except ValueError as err:
        await interaction.followup.send(embed=error_embed(str(err)))
        return

    members = sorted(clan.members, key=lambda m: m.donations, reverse=True)
    header = f"`{pad('#', 2)} {pad('Name', 15)} {pad('Don', 5)} {pad('Rec', 5)}`"
    lines = [header]
    total_don = total_rec = 0
    for i, m in enumerate(members, start=1):
        total_don += m.donations
        total_rec += m.received
        lines.append(f"`{pad_start(i, 2)} {pad(m.name, 15)} {pad_start(m.donations, 5)} {pad_start(m.received, 5)}`")

    embed = await base_embed(interaction, title=f"{clan.name} ({clan.tag}), Donations")
    embed.description = "\n".join(lines)[:4000]
    embed.set_footer(text=f"{E_DONATE} {total_don}  •  {E_RECEIVE} {total_rec}")
    await interaction.followup.send(embed=embed)
