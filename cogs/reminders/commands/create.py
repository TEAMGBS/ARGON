"""/reminders create, open the interactive config for a new reminder."""

from __future__ import annotations

import discord

from database import clans as clans_db
from utils.embeds import error_embed, format_tag

from ..duration import parse_durations
from ..state import ReminderState
from ..views import ReminderConfigView


async def handle(
    interaction: discord.Interaction,
    type_: str,
    clan_tag: str,
    time: str,
    message: str | None,
    channel: discord.TextChannel | None,
) -> None:
    tag = format_tag(clan_tag)
    clan_row = await clans_db.get_clan(interaction.guild_id, tag)
    if not clan_row:
        await interaction.response.send_message(
            embed=error_embed(f"`{tag}` is not added to this server. Use `/alliance add-clan` first."),
            ephemeral=True,
        )
        return

    try:
        timings = parse_durations(time)
    except ValueError as bad:
        await interaction.response.send_message(
            embed=error_embed(f"`{bad}` is not a valid time. Try `1h`, `30m`, `2h2m`, or `1h, 30m`."),
            ephemeral=True,
        )
        return
    if not timings:
        await interaction.response.send_message(
            embed=error_embed("Enter at least one reminder time, e.g. `1h` or `2h2m`."), ephemeral=True
        )
        return

    target_channel = channel or interaction.channel
    state = ReminderState(
        reminder_id=None,
        guild_id=interaction.guild_id,
        clan_tag=tag,
        clan_name=clan_row["name"],
        type=type_,
        channel_id=target_channel.id,
        created_by=interaction.user.id,
        message=message or "",
        timing_minutes=timings,
    )
    view = ReminderConfigView(state)
    await interaction.response.send_message(view=view)
