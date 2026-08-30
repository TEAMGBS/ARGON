"""/clan compo — Town Hall composition."""

import collections

import discord

from utils.embeds import base_embed, error_embed
from utils.emojis import E_TOWNHALL
from utils.helpers import pad_start
from utils.resolver import resolve_clan


async def compo(interaction: discord.Interaction, tag: str = None):
    await interaction.response.defer()
    try:
        clan = await resolve_clan(interaction, tag)
    except ValueError as err:
        await interaction.followup.send(embed=error_embed(str(err)))
        return

    # ClanMember carries the town hall level, so no extra per-player lookups needed.
    counts = collections.Counter(m.town_hall for m in clan.members)
    rows = [f"{E_TOWNHALL} `TH{pad_start(th, 2)}` — **{n}**" for th, n in sorted(counts.items(), reverse=True)]

    embed = await base_embed(interaction, title=f"{clan.name} ({clan.tag}) — Composition")
    embed.description = "\n".join(rows) or "_No data._"
    embed.set_footer(text=f"{clan.member_count} members")
    await interaction.followup.send(embed=embed)
