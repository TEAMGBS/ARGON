"""Background poller for Legend League tracking.

Every ~2 minutes it fetches each tracked player, diffs their trophy count against
the last snapshot, and records a rise as an attack and a fall as a defense, then
posts a notification to every guild tracking that player. First sight of a player
(or a new season) only seeds the baseline - there is no back-fill of past attacks.
"""

from __future__ import annotations

import traceback

import discord
from discord.ext import commands, tasks

from database import ranked as ranked_db

from .notify import build_notification
from .season import season_key, week_start

# Trophy swings larger than this are treated as anomalies (season reset, league
# promotion/demotion, data glitch) and never recorded as an attack/defense.
_MAX_SANE_DELTA = 500

POLL_SECONDS = 120


class RankedTracker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        self.poll.start()

    async def cog_unload(self):
        self.poll.cancel()

    @tasks.loop(seconds=POLL_SECONDS)
    async def poll(self):
        try:
            await self._run()
        except Exception:
            print("[ranked] poll tick failed:\n" + traceback.format_exc())

    @poll.before_loop
    async def _before(self):
        await self.bot.wait_until_ready()

    async def _run(self):
        # Ranked attacks reset weekly; drop anything from before this week.
        try:
            await ranked_db.prune_events_before(week_start())
        except Exception:
            pass

        tags = await ranked_db.all_tracked_tags()
        if not tags:
            return
        season = season_key()
        for tag in tags:
            try:
                await self._poll_tag(tag, season)
            except Exception:
                print(f"[ranked] error polling {tag}:\n" + traceback.format_exc())

    async def _poll_tag(self, tag: str, season: str):
        try:
            player = await self.bot.coc_client.get_player(tag)
        except Exception as exc:
            print(f"[ranked] {tag}: could not fetch player: {exc!r}")
            return

        trophies = player.trophies
        name = player.name

        state = await ranked_db.get_state(tag)

        # First sight or a new season: seed the baseline, record nothing.
        if state is None or state["season"] != season:
            await ranked_db.set_state(tag, name, trophies, season)
            return

        prev = state["trophies"]
        if trophies == prev:
            if name != state["name"]:
                await ranked_db.set_state(tag, name, trophies, season)
            return

        # Record trophy moves in every league (a rise is an attack, a fall a
        # defense). The sane-delta guard skips season resets and other anomalies.
        delta = trophies - prev
        if abs(delta) <= _MAX_SANE_DELTA:
            direction = "attack" if delta > 0 else "defense"
            await ranked_db.add_event(tag, season, direction, delta, trophies)
            await self._notify(tag, name, direction, delta, trophies)
            print(f"[ranked] {tag} ({name}): {direction} {delta:+d} -> {trophies}")

        await ranked_db.set_state(tag, name, trophies, season)

    async def _notify(self, tag: str, name: str, direction: str, delta: int, trophies_after: int):
        content = await build_notification(tag, name, direction, delta, trophies_after)
        for row in await ranked_db.guilds_tracking(tag):
            channel_id = int(row["channel_id"])
            channel = self.bot.get_channel(channel_id)
            if channel is None:
                try:
                    channel = await self.bot.fetch_channel(channel_id)
                except Exception as exc:
                    print(f"[ranked] channel {channel_id} (guild {row['guild_id']}): cannot access: {exc!r}")
                    continue
            if not isinstance(channel, discord.abc.Messageable):
                continue
            try:
                await channel.send(content=content[:2000])
            except discord.Forbidden:
                print(f"[ranked] channel {channel_id} (guild {row['guild_id']}): missing permission to send.")
            except Exception as exc:
                print(f"[ranked] channel {channel_id} (guild {row['guild_id']}): send failed: {exc!r}")
