"""/clan boosts, active Super Troop boosts among clan members."""

import asyncio

import discord

from utils.embeds import base_embed, error_embed
from utils.emojis import E_TROOP
from utils.resolver import resolve_clan
from utils.units import active_super_troops


async def boosts(interaction: discord.Interaction, tag: str = None):
    await interaction.response.defer()
    try:
        clan = await resolve_clan(interaction, tag)
    except ValueError as err:
        await interaction.followup.send(embed=error_embed(str(err)))
        return

    coc_client = interaction.client.coc_client

    async def fetch(member_tag):
        try:
            return await coc_client.get_player(member_tag)
        except Exception:
            return None

    players = await asyncio.gather(*(fetch(m.tag) for m in clan.members))

    boost_map: dict[str, list[str]] = {}
    for p in players:
        if not p:
            continue
        for troop in active_super_troops(p):
            boost_map.setdefault(troop["name"], []).append(p.name)

    embed = await base_embed(interaction, title=f"{clan.name} ({clan.tag}), Active Boosts")
    if not boost_map:
        embed.description = "No active Super Troop boosts right now."
    else:
        blocks = []
        for troop_name, names in boost_map.items():
            listing = "\n".join(f"• {n}" for n in names)
            blocks.append(f"{E_TROOP} **{troop_name}**, {len(names)}\n{listing}")
        embed.description = "\n\n".join(blocks)[:4000]

    await interaction.followup.send(embed=embed)
