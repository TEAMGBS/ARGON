"""/player rushed, estimate under-levelled units.

Without the full offline max-level-per-TH tables we use a conservative heuristic
(units below 60% of their current max) and clearly label it as an estimate.
Units are read from the raw API payload (see utils/units) to avoid coc.py's
game-data IndexError on newly added levels.
"""

import discord

from utils.embeds import base_embed, error_embed
from utils.helpers import pad, pad_start
from utils.resolver import resolve_player
from utils.units import home_units


async def rushed(interaction: discord.Interaction, tag: str = None, user: discord.User = None):
    await interaction.response.defer()
    try:
        player = await resolve_player(interaction, tag, user)
    except ValueError as err:
        await interaction.followup.send(embed=error_embed(str(err)))
        return

    units = [*home_units(player, "heroes"), *home_units(player, "troops"), *home_units(player, "spells")]
    rushed_units = [u for u in units if 0 < u["level"] < int(u["maxLevel"] * 0.6)]

    embed = await base_embed(interaction, title=f"{player.name} ({player.tag}), Rushed (estimate)")
    if not rushed_units:
        embed.description = "No significantly under-levelled units detected. 👍"
    else:
        embed.description = "\n".join(
            f"`{pad(u['name'], 18)} {pad_start(u['level'], 2)}/{pad_start(u['maxLevel'], 2)}`" for u in rushed_units
        )[:4000]
        embed.set_footer(text="Heuristic estimate, units below 60% of current max level.")

    await interaction.followup.send(embed=embed)
