"""/clan search, find public clans by name."""

import discord

from utils.embeds import base_embed, error_embed
from utils.emojis import E_CLAN, E_PEOPLE, E_TROPHY


async def search(interaction: discord.Interaction, name: str):
    await interaction.response.defer()
    try:
        results = await interaction.client.coc_client.search_clans(name=name, limit=10)
    except Exception:
        await interaction.followup.send(embed=error_embed("Clash of Clans API request failed, try again in a bit."))
        return

    if not results:
        await interaction.followup.send(embed=error_embed("No clans found for that name."))
        return

    lines = [
        f"{E_CLAN} **{c.name}** ({c.tag}), Lv {c.level} • {E_PEOPLE} {c.member_count}/50 • {E_TROPHY} {c.points}"
        for c in results
    ]
    embed = await base_embed(interaction, title=f'Clan search, "{name}"')
    embed.description = "\n".join(lines)[:4000]
    await interaction.followup.send(embed=embed)
