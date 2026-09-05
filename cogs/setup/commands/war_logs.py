"""/setup war-logs, post a clan's attack feed and war-phase embeds to a channel."""

from __future__ import annotations

import discord

from cogs.reminders.duration import format_minutes, parse_durations
from database import clans as clans_db
from database import warlogs as warlogs_db
from utils.embeds import error_embed, success_embed
from utils.tags import normalize_tag


async def handle(
    interaction: discord.Interaction,
    clan: str,
    type: str | None = None,
    time: str | None = None,
    channel: discord.TextChannel | None = None,
) -> None:
    await interaction.response.defer()
    tag = normalize_tag(clan)

    row = await clans_db.get_clan(interaction.guild_id, tag)
    if not row:
        await interaction.followup.send(
            embed=error_embed(f"`{tag}` is not an alliance clan. Add it first with `/alliance add-clan`.")
        )
        return

    timings = None
    if time:
        try:
            timings = parse_durations(time)
        except ValueError as err:
            await interaction.followup.send(embed=error_embed(str(err)))
            return

    war_type = type or ""  # "" means every war type
    target = channel or interaction.channel
    log_id = await warlogs_db.set_channel(interaction.guild_id, tag, target.id, war_type, timings)

    scope = f"**{war_type.upper()}** wars" if war_type else "**all** war types"
    marks = ", ".join(format_minutes(m) for m in (timings or [1080, 720, 360]))
    await interaction.followup.send(
        embed=success_embed(
            f"War logs for **{row['name']}** (`{tag}`) → {target.mention} ({scope}).\n"
            f"Every war hit is posted there, plus a war-info embed at prep, war start, "
            f"{marks} left, and war end.\nID: `{log_id}` — edit with `/setup edit-war-logs`, remove with `/setup rmwar-log`."
        )
    )
