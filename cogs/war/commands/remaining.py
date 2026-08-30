"""/war remaining — members with attacks left."""

import coc
import discord

from utils.embeds import base_embed, error_embed
from utils.emojis import E_SWORD
from utils.helpers import discord_relative
from utils.resolver import resolve_clan


async def remaining(interaction: discord.Interaction, tag: str = None):
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

    per_member = war.attacks_per_member or 2
    laggards = []
    for m in sorted(war.clan.members, key=lambda x: x.map_position):
        used = len(m.attacks)
        if used < per_member:
            laggards.append(f"{E_SWORD} **{m.name}** — {per_member - used} left")

    embed = await base_embed(interaction, title=f"{war.clan.name} — Remaining Attacks")
    embed.description = "\n".join(laggards)[:4000] if laggards else "All attacks used! 🎉"
    if war.state == "preparation":
        embed.add_field(name="Battle day", value=discord_relative(war.start_time.time), inline=False)
    else:
        embed.add_field(name="War ends", value=discord_relative(war.end_time.time), inline=False)

    await interaction.followup.send(embed=embed)
