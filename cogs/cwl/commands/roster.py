"""/cwl roster — the CWL season's participating clans."""

import coc
import discord

from utils.embeds import base_embed, error_embed
from utils.emojis import E_CLAN
from utils.helpers import pad_start
from utils.resolver import resolve_clan


async def roster(interaction: discord.Interaction, tag: str = None):
    await interaction.response.defer()
    try:
        clan = await resolve_clan(interaction, tag)
    except ValueError as err:
        await interaction.followup.send(embed=error_embed(str(err)))
        return

    try:
        group = await interaction.client.coc_client.get_league_group(clan.tag)
    except coc.NotFound:
        await interaction.followup.send(embed=error_embed("This clan is not in a Clan War League season right now."))
        return
    except Exception:
        await interaction.followup.send(embed=error_embed("Clash of Clans API request failed, try again in a bit."))
        return

    clans = sorted(group.clans, key=lambda c: c.level, reverse=True)
    lines = [f"`{pad_start(i, 2)}` {E_CLAN} **{c.name}** ({c.tag}) — Lv {c.level}" for i, c in enumerate(clans, 1)]

    embed = await base_embed(interaction, title=f"{clan.name} — CWL Season ({group.season})")
    embed.description = "\n".join(lines)[:4000]
    embed.set_footer(text=f"{len(group.clans)} clans • {group.number_of_rounds} rounds")
    await interaction.followup.send(embed=embed)
