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

from database import warlogs as warlogs_db

from .warembed import attack_lines, build_war_embed

POLL_SECONDS = 60
_THRESHOLDS = (18, 12, 6)


def _war_key(war) -> str:
    war_tag = getattr(war, "war_tag", None)
    if war_tag:
        return str(war_tag)
    prep = getattr(war, "preparation_start_time", None)
    if prep is not None and getattr(prep, "raw_time", None):
        return prep.raw_time
    end = getattr(war, "end_time", None)
    return getattr(end, "raw_time", None) or "current"


def _applicable_events(war) -> list[str]:
    """Phase events that are currently true for this war."""
    state = war.state
    events: list[str] = []
    if state == "preparation":
        events.append("prep")
    elif state == "inWar":
        events.append("start")
        hours_left = war.end_time.seconds_until / 3600
        events += [f"{th}h" for th in _THRESHOLDS if hours_left <= th]
    elif state == "warEnded":
        events.append("end")
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
        applicable = _applicable_events(war)
        lines, current_max = attack_lines(war, since_order=0)  # full list; per-guild we filter by last_order

        for row in channels:
            await self._process_guild(row["guild_id"], row["channel_id"], tag, war, war_key, applicable, current_max)

    async def _process_guild(self, guild_id, channel_id, tag, war, war_key, applicable, current_max):
        progress = await warlogs_db.get_progress(guild_id, tag, war_key)

        if progress is None:
            # First time we see this war for this guild: seed so we don't back-fill
            # old attacks, but post one embed for the current phase.
            posted = list(applicable)
            await warlogs_db.set_progress(guild_id, tag, war_key, current_max, posted)
            if applicable:
                await self._send(channel_id, embed=build_war_embed(war, applicable[-1]))
            return

        posted = list(progress["events"] or [])
        last_order = progress["last_order"] or 0

        # New phase embeds.
        new_events = [e for e in applicable if e not in posted]
        for event in new_events:
            await self._send(channel_id, embed=build_war_embed(war, event))
            posted.append(event)

        # New attack/defense feed lines.
        lines, new_max = attack_lines(war, since_order=last_order)
        for chunk in _chunk_lines(lines):
            await self._send(channel_id, content=chunk)

        await warlogs_db.set_progress(guild_id, tag, war_key, max(last_order, new_max), posted)

    async def _send(self, channel_id, *, content=None, embed=None):
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
            await channel.send(content=content, embed=embed)
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
