"""/alliance info-clans, show live details for each clan added to this server."""

from __future__ import annotations

import asyncio

import discord

from database import clans as clans_db
from utils.embeds import base_embed, error_embed
from utils.emojis import E_CLAN, E_PEOPLE, E_TROPHY


async def handle(interaction: discord.Interaction) -> None:
    await interaction.response.defer()
    rows = await clans_db.get_clans_for_guild(interaction.guild_id)
    if not rows:
        await interaction.followup.send(embed=error_embed("No clans added yet. Use `/alliance add-clan`."))
        return

    coc_client = interaction.client.coc_client

    async def fetch(tag):
        try:
            return await coc_client.get_clan(tag)
        except Exception:
            return None

    clans = await asyncio.gather(*(fetch(row["tag"]) for row in rows))

    embed = await base_embed(interaction, title="Alliance Clans, Info")
    for row, clan in zip(rows, clans):
        if clan is None:
            embed.add_field(name=f"{row['name']} ({row['tag']})", value="_Could not fetch live data._", inline=False)
            continue
        league = clan.war_league.name if clan.war_league else "Unranked"
        embed.add_field(
            name=f"{E_CLAN} {clan.name} ({clan.tag})",
            value=(
                f"Level {clan.level} • {E_PEOPLE} {clan.member_count}/50 • {E_TROPHY} {clan.points}\n"
                f"War league: {league} • War wins: {clan.war_wins}"
            ),
            inline=False,
        )

    embed.set_footer(text=f"{len(rows)} clan(s)")
    await interaction.followup.send(embed=embed)
