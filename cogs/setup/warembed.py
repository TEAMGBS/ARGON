"""Build the war-info embed and the per-attack feed lines.

Attack lines look like (with custom emojis):
    {sword} `barbarian king` {vs} `CRAZY DIBYA` : {star}{star}{star} `100%`
    {shield} `Swapnil` {vs} `ashen one` : {star}{star}{emptystar} `78%`
"""

from __future__ import annotations

import discord

from utils.emojis import E_SHIELD_ICON, E_SWORD_ICON, E_VS, war_stars
from utils.helpers import discord_relative

# Colours per phase.
PREP = 0x5865F2
BATTLE = 0xE67E22
ENDING = 0xE74C3C
ENDED_WIN = 0x57F287
ENDED_LOSE = 0xED4245
ENDED_TIE = 0xFEE75C

def _attacks_used(side) -> int:
    return sum(len(getattr(m, "attacks", []) or []) for m in getattr(side, "members", []) or [])


def _side_value(war, side) -> str:
    total = getattr(war, "team_size", 0) * (getattr(war, "attacks_per_member", 2) or 2)
    used = _attacks_used(side)
    stars = getattr(side, "stars", 0)
    destruction = getattr(side, "destruction", 0.0) or 0.0
    return f"⭐ {stars}  •  💥 {destruction:.1f}%  •  ⚔️ {used}/{total}"


def _result(war) -> tuple[str, int]:
    clan, opp = war.clan, war.opponent
    cs, os_ = getattr(clan, "stars", 0), getattr(opp, "stars", 0)
    cd, od = getattr(clan, "destruction", 0.0) or 0.0, getattr(opp, "destruction", 0.0) or 0.0
    if cs > os_ or (cs == os_ and cd > od):
        return "🎉 Victory", ENDED_WIN
    if cs < os_ or (cs == os_ and cd < od):
        return "💀 Defeat", ENDED_LOSE
    return "🤝 Draw", ENDED_TIE


def build_war_embed(war, label: str, color: int, ended: bool = False) -> discord.Embed:
    if ended:
        label, color = _result(war)

    embed = discord.Embed(title=f"{war.clan.name}  vs  {war.opponent.name}", description=f"**{label}**", color=color)
    embed.add_field(name=war.clan.name, value=_side_value(war, war.clan), inline=False)
    embed.add_field(name=war.opponent.name, value=_side_value(war, war.opponent), inline=False)

    state = war.state
    if state == "preparation" and getattr(war, "start_time", None):
        embed.add_field(name="Battle day", value=f"Starts {discord_relative(war.start_time.time)}", inline=False)
    elif state == "inWar" and getattr(war, "end_time", None):
        embed.add_field(name="War ends", value=discord_relative(war.end_time.time), inline=False)

    embed.set_footer(text=f"{war.team_size} vs {war.team_size} • {war.clan.tag}")
    if getattr(war.clan, "badge", None):
        try:
            embed.set_thumbnail(url=war.clan.badge.url)
        except Exception:
            pass
    return embed


def attack_lines(war, since_order: int) -> tuple[list[str], int]:
    """Feed lines for attacks with order > since_order, plus the new max order."""
    our_tags = {m.tag for m in war.clan.members}
    names = {m.tag: m.name for m in list(war.clan.members) + list(war.opponent.members)}

    attacks = []
    for member in list(war.clan.members) + list(war.opponent.members):
        for atk in getattr(member, "attacks", []) or []:
            attacks.append(atk)
    attacks.sort(key=lambda a: getattr(a, "order", 0))

    lines = []
    max_order = since_order
    for atk in attacks:
        order = getattr(atk, "order", 0)
        if order <= since_order:
            continue
        max_order = max(max_order, order)
        stars = war_stars(getattr(atk, "stars", 0))
        pct = int(round(getattr(atk, "destruction", 0) or 0))
        attacker, defender = atk.attacker_tag, atk.defender_tag
        if attacker in our_tags:  # our member attacked
            ours, foe, marker = names.get(attacker, attacker), names.get(defender, defender), E_SWORD_ICON
        elif defender in our_tags:  # our member was attacked
            ours, foe, marker = names.get(defender, defender), names.get(attacker, attacker), E_SHIELD_ICON
        else:
            continue
        lines.append(f"{marker} `{ours}` {E_VS} `{foe}` : {stars} `{pct}%`")
    return lines, max_order
