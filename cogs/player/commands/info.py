"""/player info — profile card."""

import discord

from utils.embeds import base_embed, error_embed
from utils.emojis import (
    E_CLAN,
    E_DONATE,
    E_HERO,
    E_RECEIVE,
    E_SHIELD,
    E_STAR,
    E_SWORD,
    E_TROPHY,
    E_XP,
    get_th_emoji,
)
from utils.resolver import resolve_player


async def info(interaction: discord.Interaction, tag: str = None, user: discord.User = None):
    await interaction.response.defer()
    try:
        player = await resolve_player(interaction, tag, user)
    except ValueError as err:
        await interaction.followup.send(embed=error_embed(str(err)))
        return

    embed = await base_embed(interaction, title=f"{player.name} ({player.tag})")
    embed.url = f"https://link.clashofclans.com/en?action=OpenPlayerProfile&tag={player.tag.replace('#', '%23')}"
    embed.add_field(name="Town Hall", value=get_th_emoji(player.town_hall), inline=True)
    embed.add_field(name="XP Level", value=f"{E_XP} {player.exp_level}", inline=True)
    embed.add_field(name="Trophies", value=f"{E_TROPHY} {player.trophies} (best {player.best_trophies})", inline=True)
    embed.add_field(name="War Stars", value=f"{E_STAR} {player.war_stars}", inline=True)
    embed.add_field(name="Attacks Won", value=f"{E_SWORD} {player.attack_wins}", inline=True)
    embed.add_field(name="Defenses Won", value=f"{E_SHIELD} {player.defense_wins}", inline=True)

    if player.clan is not None:
        role = getattr(player, "role", None)
        role_name = role.in_game_name if role else "Member"
        embed.add_field(name="Clan", value=f"{E_CLAN} {player.clan.name} ({player.clan.tag}) — {role_name}", inline=False)

    heroes = [h for h in player.heroes if h.is_home_base]
    if heroes:
        embed.add_field(
            name="Heroes",
            value="\n".join(f"{E_HERO} {h.name}: **{h.level}**/{h.max_level}" for h in heroes),
            inline=False,
        )

    embed.add_field(name="Donations", value=f"{E_DONATE} {player.donations} • {E_RECEIVE} {player.received}", inline=True)

    if player.league is not None and getattr(player.league, "icon", None) is not None:
        embed.set_thumbnail(url=player.league.icon.url)

    await interaction.followup.send(embed=embed)
