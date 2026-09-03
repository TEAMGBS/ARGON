"""/reminders list, show active reminders grouped by clan."""

from __future__ import annotations

import discord

from database import clans as clans_db
from database import reminders as reminders_db

from ..constants import TYPE_LABELS


async def handle(interaction: discord.Interaction) -> None:
    rows = await reminders_db.get_reminders_for_guild(interaction.guild_id)
    if not rows:
        await interaction.response.send_message(
            "No active reminders configured for this server.", ephemeral=True
        )
        return

    clan_names: dict[str, str] = {}
    lines_by_clan: dict[str, list[str]] = {}
    for row in rows:
        tag = row["clan_tag"]
        if tag not in clan_names:
            clan_row = await clans_db.get_clan(interaction.guild_id, tag)
            clan_names[tag] = clan_row["name"] if clan_row else tag
        label = TYPE_LABELS.get(row["type"], row["type"])
        timing = ", ".join(f"{m}m" for m in (row["timing_minutes"] or []))
        lines_by_clan.setdefault(tag, []).append(
            f"`{row['id']}` {label}, channel <#{row['channel_id']}>, timing: {timing or 'not set'}"
        )

    view = discord.ui.LayoutView()
    container = discord.ui.Container()
    container.add_item(discord.ui.TextDisplay("**Active Reminders**"))
    for tag, lines in lines_by_clan.items():
        container.add_item(discord.ui.Separator())
        container.add_item(discord.ui.TextDisplay(f"**{clan_names[tag]}** ({tag})\n" + "\n".join(lines)))
    view.add_item(container)
    await interaction.response.send_message(view=view)
