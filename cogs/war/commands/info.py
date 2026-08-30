"""/war info, current war status."""

import coc
import discord

from utils.embeds import base_embed, error_embed
from utils.emojis import E_STAR, E_SWORD
from utils.helpers import discord_relative
from utils.resolver import resolve_clan

_STATE = {
    "preparation": "Preparation Day",
    "inWar": "Battle Day",
    "warEnded": "War Ended",
    "notInWar": "Not in War",
}


async def info(interaction: discord.Interaction, tag: str = None):
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

    embed = await base_embed(interaction, title=f"{war.clan.name} vs {war.opponent.name}")
    timing = (
        f"**Battle day:** {discord_relative(war.start_time.time)}"
        if war.state == "preparation"
        else f"**Ends:** {discord_relative(war.end_time.time)}"
    )
    embed.description = f"**State:** {_STATE.get(war.state, war.state)}\n**Team Size:** {war.team_size}v{war.team_size}\n{timing}"
    embed.add_field(
        name=war.clan.name,
        value=f"{E_STAR} {war.clan.stars}  {E_SWORD} {war.clan.attacks_used}\n💥 {war.clan.destruction:.2f}%",
        inline=True,
    )
    embed.add_field(
        name=war.opponent.name,
        value=f"{E_STAR} {war.opponent.stars}  {E_SWORD} {war.opponent.attacks_used}\n💥 {war.opponent.destruction:.2f}%",
        inline=True,
    )

    if war.state == "warEnded":
        c, o = war.clan, war.opponent
        if c.stars > o.stars or (c.stars == o.stars and c.destruction > o.destruction):
            result = "Won 🎉"
        elif c.stars == o.stars and c.destruction == o.destruction:
            result = "Draw"
        else:
            result = "Lost"
        embed.add_field(name="Result", value=result, inline=False)

    await interaction.followup.send(embed=embed)
