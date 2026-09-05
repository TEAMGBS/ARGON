"""Build the war-info board (Components V2) and the per-attack feed lines.

Attack lines look like (with custom emojis):
    {sword} `barbarian king` {vs} `CRAZY DIBYA` : {star}{star}{star} `100%`
    {shield} `Swapnil` {vs} `ashen one` : {star}{star}{emptystar} `78%`
"""

from __future__ import annotations

from collections import Counter
from urllib.parse import quote

import discord

from utils.emojis import CUSTOM, E_SHIELD_ICON, E_STAR_FULL, E_SWORD_ICON, E_VS, get_th_emoji, war_stars
from utils.helpers import discord_relative

# Colours per phase.
PREP = 0x5865F2
BATTLE = 0xE67E22
ENDING = 0xE74C3C
ENDED_WIN = 0x57F287
ENDED_LOSE = 0xED4245
ENDED_TIE = 0xFEE75C

E_PCT = CUSTOM.get("Percentage", "💥")


def _attacks_used(side) -> int:
    return sum(len(getattr(m, "attacks", []) or []) for m in getattr(side, "members", []) or [])


def _result(war) -> tuple[str, int]:
    clan, opp = war.clan, war.opponent
    cs, os_ = getattr(clan, "stars", 0), getattr(opp, "stars", 0)
    cd, od = getattr(clan, "destruction", 0.0) or 0.0, getattr(opp, "destruction", 0.0) or 0.0
    if cs > os_ or (cs == os_ and cd > od):
        return "🎉 Victory", ENDED_WIN
    if cs < os_ or (cs == os_ and cd < od):
        return "💀 Defeat", ENDED_LOSE
    return "🤝 Draw", ENDED_TIE


def _clan_link(tag: str) -> str:
    return f"https://link.clashofclans.com/en?action=OpenClanProfile&tag={quote(tag)}"


def _roster(side) -> str:
    """A clan name followed by its Town Hall composition (TH icon + count)."""
    comp = Counter(getattr(m, "town_hall", 0) for m in getattr(side, "members", []) or [])
    parts = " ".join(f"{get_th_emoji(th)} {comp[th]}" for th in sorted(comp, reverse=True) if th)
    return f"{side.name}\n{parts}\n"


def build_war_view(war, label: str, color: int, ended: bool = False) -> discord.ui.LayoutView:
    if ended:
        label, color = _result(war)

    clan, opp = war.clan, war.opponent
    size = getattr(war, "team_size", 0)
    total = size * (getattr(war, "attacks_per_member", 2) or 2)

    if ended:
        time_line = "War has ended"
    elif war.state == "preparation" and getattr(war, "start_time", None):
        time_line = f"Starts in : {discord_relative(war.start_time.time)}"
    elif getattr(war, "end_time", None):
        time_line = f"Ends in : {discord_relative(war.end_time.time)}"
    else:
        time_line = ""

    header = (
        f"## [{clan.name}]({_clan_link(clan.tag)})\n**War Against**\n[{opp.name}]({_clan_link(opp.tag)})\n\n"
        f"**War State**\n{label} ({size}v{size})\n{time_line}\n"
    )

    view = discord.ui.LayoutView(timeout=None)
    container = discord.ui.Container(accent_color=color)

    badge_url = getattr(getattr(clan, "badge", None), "url", None)
    if badge_url:
        container.add_item(discord.ui.Section(discord.ui.TextDisplay(header), accessory=discord.ui.Thumbnail(badge_url)))
    else:
        container.add_item(discord.ui.TextDisplay(header))
    container.add_item(discord.ui.Separator(visible=False))

    our_used, opp_used = _attacks_used(clan), _attacks_used(opp)
    cs, os_ = getattr(clan, "stars", 0), getattr(opp, "stars", 0)
    cd, od = getattr(clan, "destruction", 0.0) or 0.0, getattr(opp, "destruction", 0.0) or 0.0
    stats = (
        "**War stats**\n"
        f"` {our_used}/{total} ` {E_VS} `{opp_used}/{total}`\n"
        f"` {cs} ` {E_STAR_FULL} `{os_}`\n"
        f"`{cd:.2f}` {E_PCT} `{od:.2f}`\n"
    )
    container.add_item(discord.ui.TextDisplay(stats))
    container.add_item(discord.ui.Separator(visible=False))

    container.add_item(discord.ui.TextDisplay("**War Rosters**\n" + _roster(clan) + _roster(opp)))

    view.add_item(container)
    return view


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
