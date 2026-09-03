"""/alliance info-clans, a live Components-V2 overview board of the server's clans.

The board shows a welcome header (server name + logo), every clan grouped by the
category it was added under, and a select menu. Picking a clan from the menu
replies, only to that user, with a detailed card for the clan (clan / war /
capital info) pulled live from the Clash of Clans API.
"""

from __future__ import annotations

import asyncio
import time

import coc
import discord

from database import clans as clans_db
from utils.embeds import error_embed, guild_color
from utils.emojis import CUSTOM, cwl_league_emoji, get_th_emoji

from .add_clan import DEFAULT_CATEGORIES

# Categories the servers start with are shown first, in this order; anything a
# server invented afterwards follows, alphabetically.
_CATEGORY_ORDER = {name: i for i, name in enumerate(DEFAULT_CATEGORIES)}


def _category_sort_key(category: str):
    return (_CATEGORY_ORDER.get(category, len(_CATEGORY_ORDER)), category)


def _now_stamp() -> str:
    return f"<t:{int(time.time())}:f>"


def _fmt(value) -> str:
    """Render a value for a card row, using an em dash when it is missing."""
    if value is None or value == "":
        return "—"
    return str(value)


def _leader_name(clan: coc.Clan) -> str:
    for member in getattr(clan, "members", []) or []:
        if getattr(member, "role", None) == coc.Role.leader:
            return member.name
    return "—"


def _capital_stats(clan: coc.Clan):
    """(capital hall level, total district levels) from the clan's capital districts."""
    districts = getattr(clan, "capital_districts", None) or []
    if not districts:
        return None, None
    hall_level = None
    total = 0
    for district in districts:
        level = getattr(district, "hall_level", 0) or 0
        total += level
        if getattr(district, "name", "") == "Capital Peak":
            hall_level = level
    return hall_level, total


def build_clan_card(clan: coc.Clan, color: discord.Color) -> discord.ui.LayoutView:
    """The detailed, single-clan card shown when a clan is picked from the menu."""
    league_name = clan.war_league.name if getattr(clan, "war_league", None) else "Unranked"
    league_icon = cwl_league_emoji(league_name)
    th_level = getattr(clan, "required_townhall_level", None)
    th = f"{get_th_emoji(th_level)} TH{th_level}" if th_level else "Any"
    location = clan.location.name if getattr(clan, "location", None) else "—"

    # War/tie totals are only exposed when a clan's war log is public.
    if getattr(clan, "public_war_log", False):
        wins, losses, ties = clan.war_wins, getattr(clan, "war_losses", None), getattr(clan, "war_ties", None)
    else:
        wins, losses, ties = getattr(clan, "war_wins", None), "🔒 Private", "🔒 Private"

    capital_league = getattr(clan, "capital_league", None)
    capital_league_name = capital_league.name if capital_league else "—"
    capital_hall, capital_total = _capital_stats(clan)

    description = (clan.description or "No description set.").strip()

    view = discord.ui.LayoutView(timeout=None)
    container = discord.ui.Container(accent_color=color)

    container.add_item(
        discord.ui.Section(
            discord.ui.TextDisplay(f"### {clan.name}\n➜ {description}"),
            accessory=discord.ui.Thumbnail(clan.badge.url),
        )
    )
    container.add_item(discord.ui.Separator(visible=False))
    container.add_item(
        discord.ui.TextDisplay(
            "**CLAN INFO**\n"
            f"> Clan leader : {_leader_name(clan)}\n"
            f"> Clan location : {location}\n"
            f"> Requirements : {th}"
        )
    )
    container.add_item(discord.ui.Separator(visible=True))
    container.add_item(
        discord.ui.TextDisplay(
            "**WAR INFO**\n"
            f"> CWL league : {league_icon} {league_name}\n"
            f"> War win streak: {_fmt(getattr(clan, 'war_win_streak', None))}\n"
            f"> Wins : {_fmt(wins)}\n"
            f"> Lose : {_fmt(losses)}\n"
            f"> Tie : {_fmt(ties)}"
        )
    )
    container.add_item(discord.ui.Separator(visible=True))
    container.add_item(
        discord.ui.TextDisplay(
            "**CAPITAL INFO**\n"
            f"> Capital League : {_fmt(capital_league_name)}\n"
            f"> Capital level : {_fmt(capital_hall)}\n"
            f"> Total upgrades : {_fmt(capital_total)}"
        )
    )
    container.add_item(discord.ui.Separator(visible=False))
    container.add_item(discord.ui.TextDisplay(f"-# {_now_stamp()}"))

    view.add_item(container)
    return view


class ClanSelect(discord.ui.Select):
    def __init__(self, options: list[discord.SelectOption], color: discord.Color) -> None:
        super().__init__(placeholder="Make a selection", min_values=1, max_values=1, options=options)
        self._color = color

    async def callback(self, interaction: discord.Interaction) -> None:
        tag = self.values[0]
        await interaction.response.defer(ephemeral=True, thinking=True)
        try:
            clan = await interaction.client.coc_client.get_clan(tag)
        except Exception:
            await interaction.followup.send(
                embed=error_embed("Could not fetch that clan right now, try again in a bit."), ephemeral=True
            )
            return
        await interaction.followup.send(view=build_clan_card(clan, self._color), ephemeral=True)


class AllianceBoard(discord.ui.LayoutView):
    """The public alliance overview board."""

    def __init__(
        self,
        *,
        guild: discord.Guild,
        rows,
        clans: list[coc.Clan | None],
        color: discord.Color,
    ) -> None:
        super().__init__(timeout=None)

        pairs = list(zip(rows, clans))
        total_players = sum((c.member_count or 0) for c in clans if c is not None)

        container = discord.ui.Container(accent_color=color)

        # ── Welcome header (server name + logo) ──────────────────────────────
        blurb = (guild.description or "").strip() or (
            f"Welcome to **{guild.name}**. Browse our clans below and pick one from the menu for full details."
        )
        header_text = discord.ui.TextDisplay(f"## WELCOME TO {guild.name.upper()}\n➜ {blurb}")
        icon_url = guild.icon.url if guild.icon else None
        if icon_url:
            container.add_item(discord.ui.Section(header_text, accessory=discord.ui.Thumbnail(icon_url)))
        else:
            container.add_item(header_text)

        container.add_item(discord.ui.Separator(visible=False))

        # ── Clans grouped by category ────────────────────────────────────────
        grouped: dict[str, list] = {}
        for row, clan in pairs:
            grouped.setdefault(row["category"], []).append((row, clan))

        lines = ["### OUR CLANS"]
        for category in sorted(grouped, key=_category_sort_key):
            lines.append(f"**{category.upper()}**")
            for row, clan in grouped[category]:
                if clan is None:
                    lines.append(f"> {CUSTOM.get('blank', '•')} {row['name']} (offline)")
                    continue
                icon = cwl_league_emoji(clan.war_league.name if getattr(clan, "war_league", None) else "")
                icon = icon or CUSTOM.get("blank", "")
                lines.append(f"> {icon} {clan.name} ({clan.member_count}/50)".rstrip())
        container.add_item(discord.ui.TextDisplay("\n".join(lines)[:4000]))

        container.add_item(discord.ui.Separator(visible=False))

        # ── Select menu (first 25 clans) ─────────────────────────────────────
        options: list[discord.SelectOption] = []
        for row, clan in pairs[:25]:
            name = clan.name if clan is not None else row["name"]
            option = discord.SelectOption(label=name[:100], value=row["tag"], description=row["tag"])
            if clan is not None and getattr(clan, "war_league", None):
                emoji_str = cwl_league_emoji(clan.war_league.name)
                if emoji_str:
                    try:
                        option.emoji = discord.PartialEmoji.from_str(emoji_str)
                    except Exception:
                        pass
            options.append(option)

        if options:
            action_row = discord.ui.ActionRow()
            action_row.add_item(ClanSelect(options, color))
            container.add_item(action_row)
            container.add_item(discord.ui.Separator(visible=False))

        # ── Footer: total players | total clans | time ───────────────────────
        container.add_item(
            discord.ui.TextDisplay(f"-# {total_players} players | {len(rows)} clans | {_now_stamp()}")
        )

        self.add_item(container)


async def handle(interaction: discord.Interaction) -> None:
    await interaction.response.defer()
    rows = await clans_db.get_clans_for_guild(interaction.guild_id)
    if not rows:
        await interaction.followup.send(embed=error_embed("No clans added yet. Use `/alliance add-clan`."))
        return

    coc_client = interaction.client.coc_client

    async def fetch(tag):
        try:
            return await coc_client.get_clan(tag)
        except Exception:
            return None

    clans = await asyncio.gather(*(fetch(row["tag"]) for row in rows))
    color = await guild_color(interaction.guild_id)
    board = AllianceBoard(guild=interaction.guild, rows=rows, clans=clans, color=color)
    await interaction.followup.send(view=board)
