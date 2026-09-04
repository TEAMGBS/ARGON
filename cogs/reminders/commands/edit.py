"""/reminders edit, reopen the config panel for an existing reminder.

Optional time/message/channel arguments are applied up front; everything else
(filters, war types) is tweaked in the panel, and Save updates the reminder in
place since its id is already set.
"""

from __future__ import annotations

import discord

from database import clans as clans_db
from database import reminders as reminders_db
from utils.embeds import error_embed

from ..duration import parse_durations
from ..state import ReminderState
from ..views import ReminderConfigView


async def handle(
    interaction: discord.Interaction,
    reminder_id: str,
    time: str | None = None,
    message: str | None = None,
    channel: discord.TextChannel | None = None,
) -> None:
    reminder_id = reminder_id.strip().upper()
    row = await reminders_db.get_reminder(reminder_id)
    if not row or row["guild_id"] != interaction.guild_id:
        await interaction.response.send_message(
            embed=error_embed(f"No reminder with id `{reminder_id}` on this server. Check `/reminders list`."),
            ephemeral=True,
        )
        return

    clan_row = await clans_db.get_clan(interaction.guild_id, row["clan_tag"])
    clan_name = clan_row["name"] if clan_row else row["clan_tag"]
    state = ReminderState.from_row(row, clan_name)

    if time is not None:
        try:
            timings = parse_durations(time)
        except ValueError as err:
            await interaction.response.send_message(embed=error_embed(str(err)), ephemeral=True)
            return
        if not timings:
            await interaction.response.send_message(
                embed=error_embed("Enter at least one reminder time, e.g. `1h` or `2h30m`."), ephemeral=True
            )
            return
        state.timing_minutes = timings
    if message is not None:
        state.message = message
    if channel is not None:
        state.channel_id = channel.id

    view = ReminderConfigView(state)
    await interaction.response.send_message(view=view, ephemeral=True)
