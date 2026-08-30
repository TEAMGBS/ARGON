"""/player army — maxed progress across heroes, troops and spells."""

import discord

from utils.embeds import base_embed, error_embed
from utils.emojis import E_HERO, E_SPELL, E_TROOP
from utils.resolver import resolve_player
from utils.units import home_units


def _progress(items) -> str:
    if not items:
        return "—"
    maxed = sum(1 for i in items if i["level"] >= i["maxLevel"])
    pct = round(maxed / len(items) * 100)
    return f"{maxed}/{len(items)} maxed ({pct}%)"


async def army(interaction: discord.Interaction, tag: str = None, user: discord.User = None):
    await interaction.response.defer()
    try:
        player = await resolve_player(interaction, tag, user)
    except ValueError as err:
        await interaction.followup.send(embed=error_embed(str(err)))
        return

    embed = await base_embed(interaction, title=f"{player.name} ({player.tag}) — Army Progress")
    embed.add_field(name=f"{E_HERO} Heroes", value=_progress(home_units(player, "heroes")), inline=True)
    embed.add_field(name=f"{E_TROOP} Troops", value=_progress(home_units(player, "troops")), inline=True)
    embed.add_field(name=f"{E_SPELL} Spells", value=_progress(home_units(player, "spells")), inline=True)

    await interaction.followup.send(embed=embed)
