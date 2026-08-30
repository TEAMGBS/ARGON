"""/war lineup, both sides ordered by map position."""

import coc
import discord

from utils.embeds import base_embed, error_embed
from utils.helpers import pad, pad_start
from utils.resolver import resolve_clan


def _side(members) -> str:
    ordered = sorted(members, key=lambda m: m.map_position)
    lines = [f"`{pad_start(i, 2)} TH{pad_start(m.town_hall, 2)} {pad(m.name, 15)}`" for i, m in enumerate(ordered, 1)]
    return "\n".join(lines)[:1024]


async def lineup(interaction: discord.Interaction, tag: str = None):
    await interaction.response.defer()
    try:
        clan = await resolve_clan(interaction, tag)
    except ValueError as err:
        await interaction.followup.send(embed=error_embed(str(err)))
        return

    try:
        war = await interaction.client.coc_client.get_current_war(clan.tag)
    except coc.PrivateWarLog:
        await interaction.followup.send(embed=error_embed("This clan's war log is private."))
        return
    except Exception:
        await interaction.followup.send(embed=error_embed("Clash of Clans API request failed, try again in a bit."))
        return

    if war is None or war.state == "notInWar":
        await interaction.followup.send(embed=error_embed(f"{clan.name} is not currently in a war."))
        return

    embed = await base_embed(interaction, title=f"{war.clan.name} vs {war.opponent.name}, Lineup")
    embed.add_field(name=war.clan.name, value=_side(war.clan.members), inline=True)
    embed.add_field(name=war.opponent.name, value=_side(war.opponent.members), inline=True)
    await interaction.followup.send(embed=embed)
