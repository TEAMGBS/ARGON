"""/setup edit-war-logs, change an existing war log's type, times, or channel."""

from __future__ import annotations

import discord

from cogs.reminders.duration import format_minutes, parse_durations
from database import warlogs as warlogs_db
from utils.embeds import error_embed, success_embed

from ..lookups import WAR_TYPE_LABELS


async def handle(
    interaction: discord.Interaction,
    warlog_id: str,
    type: str | None = None,
    time: str | None = None,
    channel: discord.TextChannel | None = None,
) -> None:
    warlog_id = warlog_id.strip().upper()
    row = await warlogs_db.get_by_id(interaction.guild_id, warlog_id)
    if not row:
        await interaction.response.send_message(
            embed=error_embed(f"No war log with id `{warlog_id}` on this server."), ephemeral=True
        )
        return

    await interaction.response.defer(ephemeral=True)

    timings = list(row["timings"] or [])
    if time:
        try:
            timings = parse_durations(time)
        except ValueError as err:
            await interaction.followup.send(embed=error_embed(str(err)), ephemeral=True)
            return

    war_type = type if type is not None else row["war_type"]
    channel_id = channel.id if channel else row["channel_id"]

    # set_channel is keyed by (guild, tag) and keeps the id stable, so this edits in place.
    await warlogs_db.set_channel(interaction.guild_id, row["tag"], channel_id, war_type, timings)

    scope = WAR_TYPE_LABELS.get(war_type, war_type or "All")
    marks = ", ".join(format_minutes(m) for m in timings)
    await interaction.followup.send(
        embed=success_embed(
            f"Updated war log `{warlog_id}` for `{row['tag']}`.\n"
            f"Type: **{scope}** • Channel: <#{channel_id}> • Embeds at: {marks} left."
        ),
        ephemeral=True,
    )
