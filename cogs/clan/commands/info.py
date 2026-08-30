"""/clan info — clan overview."""

import discord

from utils.embeds import base_embed, error_embed
from utils.emojis import E_FIRE, E_PEOPLE, E_SWORD, E_TROPHY, E_XP
from utils.resolver import resolve_clan

_TYPES = {"open": "Anyone Can Join", "inviteOnly": "Invite Only", "closed": "Closed"}


async def info(interaction: discord.Interaction, tag: str = None):
    await interaction.response.defer()
    try:
        clan = await resolve_clan(interaction, tag)
    except ValueError as err:
        await interaction.followup.send(embed=error_embed(str(err)))
        return

    embed = await base_embed(interaction, title=f"{clan.name} ({clan.tag})")
    embed.url = f"https://link.clashofclans.com/en?action=OpenClanProfile&tag={clan.tag.replace('#', '%23')}"
    embed.description = clan.description or "_No description._"
    embed.add_field(name="Level", value=f"{E_XP} {clan.level}", inline=True)
    embed.add_field(name="Members", value=f"{E_PEOPLE} {clan.member_count}/50", inline=True)
    embed.add_field(name="Points", value=f"{E_TROPHY} {clan.points}", inline=True)
    embed.add_field(name="Req. Trophies", value=f"{E_TROPHY} {clan.required_trophies}", inline=True)
    embed.add_field(name="War Wins", value=f"{E_SWORD} {clan.war_wins}", inline=True)
    embed.add_field(name="Win Streak", value=f"{E_FIRE} {clan.war_win_streak}", inline=True)
    embed.add_field(name="War League", value=clan.war_league.name if clan.war_league else "Unranked", inline=True)
    embed.add_field(name="War Log", value="Public" if clan.public_war_log else "Private", inline=True)
    embed.add_field(name="Type", value=_TYPES.get(clan.type, clan.type), inline=True)
    if clan.location is not None:
        embed.add_field(name="Location", value=f"📍 {clan.location.name}", inline=True)
    if getattr(clan, "badge", None) is not None:
        embed.set_thumbnail(url=clan.badge.url)

    await interaction.followup.send(embed=embed)
