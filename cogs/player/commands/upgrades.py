"""/player upgrades, units not yet at their current max level."""

import discord

from utils.embeds import base_embed, error_embed
from utils.helpers import pad, pad_start
from utils.resolver import resolve_player
from utils.units import home_units


def _pending(items) -> str:
    pending = [u for u in items if u["level"] < u["maxLevel"]]
    if not pending:
        return "_all maxed_"
    return "\n".join(
        f"`{pad(u['name'], 18)} {pad_start(u['level'], 2)} → {pad_start(u['maxLevel'], 2)}`" for u in pending
    )[:1024]


async def upgrades(interaction: discord.Interaction, tag: str = None, user: discord.User = None):
    await interaction.response.defer()
    try:
        player = await resolve_player(interaction, tag, user)
    except ValueError as err:
        await interaction.followup.send(embed=error_embed(str(err)))
        return

    embed = await base_embed(interaction, title=f"{player.name} ({player.tag}), Upgrades Available")
    embed.add_field(name="Heroes", value=_pending(home_units(player, "heroes")), inline=False)
    embed.add_field(name="Troops", value=_pending(home_units(player, "troops")), inline=False)
    embed.add_field(name="Spells", value=_pending(home_units(player, "spells")), inline=False)

    await interaction.followup.send(embed=embed)
