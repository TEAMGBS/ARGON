"""Background poller for war logs.

Every minute it fetches the current war for each clan with a war log configured,
posts a feed line for each new attack/defense, and posts a war-info embed as the
war moves through prep, battle start, the 18h/12h/6h marks, and war end. Progress
is stored per (guild, clan, war) so nothing is posted twice; the first time a war
is seen its attacks are seeded (no back-fill) to avoid a burst of old hits.
"""

from __future__ import annotations

import traceback

import coc
import discord
from discord.ext import commands, tasks

from cogs.reminders.duration import format_minutes
from database import warlogs as warlogs_db

from .warembed import BATTLE, ENDING, PREP, attack_lines, build_war_view

POLL_SECONDS = 60


def _war_key(war) -> str:
    war_tag = getattr(war, "war_tag", None)
    if war_tag:
        return str(war_tag)
    prep = getattr(war, "preparation_start_time", None)
    if prep is not None and getattr(prep, "raw_time", None):
        return prep.raw_time
    end = getattr(war, "end_time", None)
    return getattr(end, "raw_time", None) or "current"


def _war_type(war) -> str:
    """Classify the current war as 'cwl', 'friendly', or 'normal'."""
    if getattr(war, "is_cwl", False):
        return "cwl"
    return "friendly" if getattr(war, "type", None) == "friendly" else "normal"


def _applicable(war, timings) -> list[tuple]:
    """Events currently true for this war, as (key, label, color, ended).

    `timings` are minutes-before-end marks (per war log) at which a phase embed
    is posted, in addition to prep, war start, and war end.
    """
    state = war.state
    events: list[tuple] = []
    if state == "preparation":
        events.append(("prep", "Preparation Day", PREP, False))
    elif state == "inWar":
        events.append(("start", "Battle Day — War Started", BATTLE, False))
        minutes_left = war.end_time.seconds_until / 60
        for minutes in sorted(set(timings), reverse=True):
            if minutes_left <= minutes:
                events.append((f"t{minutes}", f"Battle Day — {format_minutes(minutes)} left", ENDING, False))
    elif state == "warEnded":
        events.append(("end", "War Ended", BATTLE, True))
    return events


class WarLogScheduler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        self.poll.start()

    async def cog_unload(self):
        self.poll.cancel()

    @tasks.loop(seconds=POLL_SECONDS)
    async def poll(self):
        try:
            for tag in await warlogs_db.all_tags():
                try:
                    await self._poll_tag(tag)
                except Exception:
                    print(f"[warlog] error on {tag}:\n" + traceback.format_exc())
        except Exception:
            print("[warlog] poll tick failed:\n" + traceback.format_exc())

    @poll.before_loop
    async def _before(self):
        await self.bot.wait_until_ready()

    async def _poll_tag(self, tag: str):
        channels = await warlogs_db.channels_for_tag(tag)
        if not channels:
            return
        try:
            war = await self.bot.coc_client.get_current_war(tag)
        except coc.PrivateWarLog:
            print(f"[warlog] {tag}: war log is private, cannot read the war.")
            return
        except coc.Maintenance:
            return
        except Exception:
            print(f"[warlog] {tag}: failed to fetch war:\n" + traceback.format_exc())
            return
        if war is None or war.state == "notInWar":
            return

        war_key = _war_key(war)
        _, current_max = attack_lines(war, since_order=0)  # only need the max attack order for seeding
        war_type = _war_type(war)

        for row in channels:
            # Skip guilds that limited their war logs to a different war type.
            if row["war_type"] and row["war_type"] != war_type:
                continue
            timings = list(row["timings"] or [])
            await self._process_guild(row["guild_id"], row["channel_id"], tag, war, war_key, current_max, timings)

    async def _process_guild(self, guild_id, channel_id, tag, war, war_key, current_max, timings):
        applicable = _applicable(war, timings)
        progress = await warlogs_db.get_progress(guild_id, tag, war_key)

        if progress is None:
            # First time we see this war for this guild: seed so we don't back-fill
            # old attacks, but post one embed for the current phase.
            posted = [key for key, *_ in applicable]
            await warlogs_db.set_progress(guild_id, tag, war_key, current_max, posted)
            if applicable:
                key, label, color, ended = applicable[-1]
                await self._send(channel_id, view=build_war_view(war, label, color, ended))
            return

        posted = list(progress["events"] or [])
        last_order = progress["last_order"] or 0

        # New phase boards.
        for key, label, color, ended in applicable:
            if key in posted:
                continue
            await self._send(channel_id, view=build_war_view(war, label, color, ended))
            posted.append(key)

        # New attack/defense feed lines.
        lines, new_max = attack_lines(war, since_order=last_order)
        for chunk in _chunk_lines(lines):
            await self._send(channel_id, content=chunk)

        await warlogs_db.set_progress(guild_id, tag, war_key, max(last_order, new_max), posted)

    async def _send(self, channel_id, *, content=None, view=None):
        channel = self.bot.get_channel(int(channel_id))
        if channel is None:
            try:
                channel = await self.bot.fetch_channel(int(channel_id))
            except Exception as exc:
                print(f"[warlog] channel {channel_id}: cannot access: {exc!r}")
                return
        if not isinstance(channel, discord.abc.Messageable):
            return
        try:
            if view is not None:
                await channel.send(view=view)
            else:
                await channel.send(content=content)
        except discord.Forbidden:
            print(f"[warlog] channel {channel_id}: missing permission to send.")
        except Exception as exc:
            print(f"[warlog] channel {channel_id}: send failed: {exc!r}")


def _chunk_lines(lines: list[str], limit: int = 1900):
    chunk = ""
    for line in lines:
        if len(chunk) + len(line) + 1 > limit:
            if chunk:
                yield chunk
            chunk = line
        else:
            chunk = f"{chunk}\n{line}" if chunk else line
    if chunk:
        yield chunk
