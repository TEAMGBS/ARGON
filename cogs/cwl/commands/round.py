"""/cwl round, the clan's current CWL matchup."""

import coc
import discord

from utils.embeds import base_embed, error_embed
from utils.emojis import E_STAR
from utils.helpers import pad
from utils.resolver import resolve_clan


async def round(interaction: discord.Interaction, tag: str = None):
    await interaction.response.defer()
    try:
        clan = await resolve_clan(interaction, tag)
    except ValueError as err:
        await interaction.followup.send(embed=error_embed(str(err)))
        return

    coc_client = interaction.client.coc_client
    try:
        group = await coc_client.get_league_group(clan.tag)
    except coc.NotFound:
        await interaction.followup.send(embed=error_embed("This clan is not in a Clan War League season right now."))
        return
    except Exception:
        await interaction.followup.send(embed=error_embed("Clash of Clans API request failed, try again in a bit."))
        return

    # Walk this clan's wars newest-first and show the latest one that has started.
    latest = None
    try:
        async for war in group.get_wars_for_clan(clan.tag):
            if war.state in ("inWar", "warEnded", "preparation"):
                latest = war
    except Exception:
        latest = None

    if latest is None:
        await interaction.followup.send(embed=error_embed("Could not find an active CWL round for this clan."))
        return

    us = latest.clan if latest.clan.tag == clan.tag else latest.opponent
    them = latest.opponent if latest.clan.tag == clan.tag else latest.clan

    embed = await base_embed(interaction, title=f"{us.name} vs {them.name}, CWL Round")
    embed.description = (
        f"**State:** {latest.state}\n"
        f"{E_STAR} {us.stars} - {them.stars}\n"
        f"💥 {us.destruction:.1f}% - {them.destruction:.1f}%"
    )
    attackers = [m for m in us.members if m.attacks]
    if attackers:
        embed.add_field(
            name="Attacks",
            value="\n".join(
                f"`{pad(m.name, 15)}` {E_STAR} {m.attacks[0].stars} • {m.attacks[0].destruction}%" for m in attackers[:15]
            ),
            inline=False,
        )
    await interaction.followup.send(embed=embed)
