"""Background scheduler: fires due war reminders and posts clan feed logs.

This is the Python equivalent of ClashPerk's feed/reminder pipeline, kept simple
and self-contained: a single loop polls each linked clan and each configured
reminder. It runs inside the reminders cog and starts once the bot is ready.
"""

import json
import traceback

import discord
from discord.ext import commands, tasks

from config import POLL_INTERVAL_SECONDS
from database.db import get_pool
from utils.embeds import guild_color
from utils.emojis import E_DONATE, E_RECEIVE, E_SWORD, E_UP, E_DOWN, E_CLAN
from utils.helpers import discord_relative


class Scheduler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.poll.change_interval(seconds=max(30, POLL_INTERVAL_SECONDS))

    async def cog_load(self):
        self.poll.start()

    async def cog_unload(self):
        self.poll.cancel()

    @tasks.loop(seconds=60)
    async def poll(self):
        try:
            pool = await get_pool()
            await self._run_feeds(pool)
            await self._run_reminders(pool)
        except Exception:
            print("Scheduler tick failed:\n" + traceback.format_exc())

    @poll.before_loop
    async def _before(self):
        await self.bot.wait_until_ready()

    # ── Clan feed: member join/leave + donation deltas ────────────────────────
    async def _run_feeds(self, pool):
        rows = await pool.fetch("SELECT DISTINCT guild_id, tag FROM clan_logs")
        for row in rows:
            try:
                await self._poll_clan(pool, row["guild_id"], row["tag"])
            except Exception:
                print("feed error:\n" + traceback.format_exc())

    async def _poll_clan(self, pool, guild_id, tag):
        logs = {
            r["log_type"]: r["channel_id"]
            for r in await pool.fetch(
                "SELECT log_type, channel_id FROM clan_logs WHERE guild_id = $1 AND tag = $2", guild_id, tag
            )
        }
        if not logs:
            return

        try:
            clan = await self.bot.coc_client.get_clan(tag)
        except Exception:
            return

        current = {
            m.tag: {"name": m.name, "role": str(m.role), "donations": m.donations, "received": m.received}
            for m in clan.members
        }

        snap = await pool.fetchrow("SELECT members FROM clan_snapshots WHERE guild_id = $1 AND tag = $2", guild_id, tag)
        if snap is not None:
            previous = json.loads(snap["members"]) if isinstance(snap["members"], str) else snap["members"]
            if logs.get("member"):
                await self._post_member_changes(guild_id, logs["member"], clan.name, previous, current)
            if logs.get("donation"):
                await self._post_donation_changes(guild_id, logs["donation"], clan.name, previous, current)

        await pool.execute(
            """INSERT INTO clan_snapshots (guild_id, tag, members, updated_at) VALUES ($1, $2, $3, NOW())
               ON CONFLICT (guild_id, tag) DO UPDATE SET members = EXCLUDED.members, updated_at = NOW()""",
            guild_id,
            tag,
            json.dumps(current),
        )

    async def _post_member_changes(self, guild_id, channel_id, clan_name, prev, curr):
        joined = [t for t in curr if t not in prev]
        left = [t for t in prev if t not in curr]
        if not joined and not left:
            return
        lines = [f"{E_UP} **{curr[t]['name']}** `{t}` joined" for t in joined]
        lines += [f"{E_DOWN} **{prev[t]['name']}** `{t}` left" for t in left]
        await self._send(guild_id, channel_id, f"{E_CLAN} {clan_name} — Member Log", "\n".join(lines))

    async def _post_donation_changes(self, guild_id, channel_id, clan_name, prev, curr):
        lines = []
        for t, data in curr.items():
            before = prev.get(t)
            if not before:
                continue
            donated = data["donations"] - before["donations"]
            received = data["received"] - before["received"]
            if donated > 0:
                lines.append(f"{E_DONATE} **{data['name']}** donated `{donated}`")
            if received > 0:
                lines.append(f"{E_RECEIVE} **{data['name']}** received `{received}`")
        if lines:
            await self._send(guild_id, channel_id, f"{E_CLAN} {clan_name} — Donation Log", "\n".join(lines))

    # ── War reminders ─────────────────────────────────────────────────────────
    async def _run_reminders(self, pool):
        reminders = await pool.fetch("SELECT * FROM reminders")
        poll_minutes = max(30, POLL_INTERVAL_SECONDS) / 60
        for r in reminders:
            try:
                await self._eval_reminder(pool, r, poll_minutes)
            except Exception:
                print("reminder error:\n" + traceback.format_exc())

    async def _eval_reminder(self, pool, r, poll_minutes):
        try:
            war = await self.bot.coc_client.get_current_war(r["tag"])
        except Exception:
            return
        if war is None or war.state != "inWar":
            return

        minutes_left = war.end_time.seconds_until / 60
        target = r["minutes_before"]
        # Fire once when we enter the [target, target - poll) window.
        if minutes_left > target or minutes_left < target - poll_minutes:
            return

        fire_key = f"{war.end_time.raw_time}:{target}"
        exists = await pool.fetchval(
            "SELECT 1 FROM reminder_logs WHERE reminder_id = $1 AND fire_key = $2", r["id"], fire_key
        )
        if exists:
            return

        per_member = war.attacks_per_member or 2
        laggards = [
            f"• **{m.name}** — {per_member - len(m.attacks)} left"
            for m in war.clan.members
            if per_member - len(m.attacks) >= r["min_remaining"]
        ]
        if not laggards:
            return

        body = "\n".join(
            [r["message"], "", f"War ends {discord_relative(war.end_time.time)}.", "", *laggards[:40]]
        )
        content = f"<@&{r['role_id']}>" if r["role_id"] else None
        await self._send(r["guild_id"], r["channel_id"], f"{E_SWORD} War Reminder — {war.clan.name}", body, content)
        await pool.execute(
            "INSERT INTO reminder_logs (reminder_id, fire_key) VALUES ($1, $2) ON CONFLICT DO NOTHING",
            r["id"],
            fire_key,
        )

    # ── Helper ────────────────────────────────────────────────────────────────
    async def _send(self, guild_id, channel_id, title, description, content=None):
        channel = self.bot.get_channel(int(channel_id))
        if channel is None:
            try:
                channel = await self.bot.fetch_channel(int(channel_id))
            except Exception:
                return
        if not isinstance(channel, discord.abc.Messageable):
            return
        color = await guild_color(guild_id)
        embed = discord.Embed(title=title, description=description[:4000], color=color)
        try:
            await channel.send(content=content, embed=embed)
        except Exception:
            pass
