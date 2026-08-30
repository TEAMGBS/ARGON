"""/player units — troop, spell and hero levels."""

import discord

from utils.embeds import base_embed, error_embed
from utils.emojis import E_HERO, E_SPELL, E_TROOP
from utils.helpers import pad, pad_start
from utils.resolver import resolve_player
from utils.units import home_units


def _table(items) -> str:
    if not items:
        return "_none_"
    lines = [f"`{pad(u['name'], 18)} {pad_start(u['level'], 2)}/{pad_start(u['maxLevel'], 2)}`" for u in items]
    return "\n".join(lines)[:1024]


async def units(interaction: discord.Interaction, tag: str = None, user: discord.User = None):
    await interaction.response.defer()
    try:
        player = await resolve_player(interaction, tag, user)
    except ValueError as err:
        await interaction.followup.send(embed=error_embed(str(err)))
        return

    embed = await base_embed(interaction, title=f"{player.name} ({player.tag}) — Units")
    embed.add_field(name=f"{E_HERO} Heroes", value=_table(home_units(player, "heroes")), inline=False)
    embed.add_field(name=f"{E_TROOP} Troops", value=_table(home_units(player, "troops")), inline=False)
    embed.add_field(name=f"{E_SPELL} Spells", value=_table(home_units(player, "spells")), inline=False)

    await interaction.followup.send(embed=embed)
