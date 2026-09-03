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

# Map the raw Clash of Clans API role value to the values stored by the reminder
# config (the API uses "admin" for what the game shows as Elder).
_API_TO_ROLE = {
    "leader": "leader",
    "coLeader": "coLeader",
    "admin": "elder",
    "member": "member",
}


def _role_value(role) -> str:
    return _API_TO_ROLE.get(getattr(role, "value", str(role)), "")


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
        await self._send(guild_id, channel_id, f"{E_CLAN} {clan_name}, Member Log", "\n".join(lines))

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
            await self._send(guild_id, channel_id, f"{E_CLAN} {clan_name}, Donation Log", "\n".join(lines))

    # ── Reminders ─────────────────────────────────────────────────────────────
    async def _run_reminders(self, pool):
        reminders = await pool.fetch("SELECT * FROM reminders")
        poll_minutes = max(30, POLL_INTERVAL_SECONDS) / 60
        for r in reminders:
            try:
                # Only war reminders fire for now; capital/cg firing is a roadmap
                # item (their attack/points data pipelines are not built yet).
                if r["type"] == "war":
                    await self._eval_war_reminder(pool, r, poll_minutes)
            except Exception:
                print("reminder error:\n" + traceback.format_exc())

    async def _eval_war_reminder(self, pool, r, poll_minutes):
        try:
            war = await self.bot.coc_client.get_current_war(r["clan_tag"])
        except Exception:
            return
        if war is None or war.state != "inWar":
            return

        minutes_left = war.end_time.seconds_until / 60
        timings = r["timing_minutes"] or []
        for timing in timings:
            # Fire once when we enter the [timing - poll, timing] window.
            if not (timing - poll_minutes <= minutes_left <= timing):
                continue

            fire_key = f"{war.end_time.raw_time}:{timing}"
            exists = await pool.fetchval(
                "SELECT 1 FROM reminder_logs WHERE reminder_id = $1 AND fire_key = $2", r["id"], fire_key
            )
            if exists:
                continue

            laggards = await self._war_laggards(r, war)
            if not laggards:
                # Still record the fire so we don't re-check this window every tick.
                await self._mark_fired(pool, r["id"], fire_key)
                continue

            body = "\n".join(
                [line for line in (r["message"],) if line]
                + ["", f"War ends {discord_relative(war.end_time.time)}.", "", *laggards[:40]]
            )
            await self._send(r["guild_id"], r["channel_id"], f"{E_SWORD} War Reminder, {war.clan.name}", body)
            await self._mark_fired(pool, r["id"], fire_key)

    async def _war_laggards(self, r, war) -> list[str]:
        per_member = war.attacks_per_member or 2
        remaining_filter = set(r["remaining_filter"] or [])
        townhalls = set(r["townhalls"] or [])
        roles = set(r["roles"] or [])
        filtered = r["member_scope"] == "filtered"

        # Only fetch clan roles when a role filter is actually set.
        role_by_tag: dict[str, str] = {}
        if filtered and roles:
            try:
                clan = await self.bot.coc_client.get_clan(r["clan_tag"])
                role_by_tag = {m.tag: _role_value(m.role) for m in clan.members}
            except Exception:
                role_by_tag = {}

        lines = []
        for m in war.clan.members:
            remaining = per_member - len(m.attacks)
            if remaining <= 0:
                continue
            if remaining_filter and remaining not in remaining_filter:
                continue
            if filtered:
                if townhalls and m.town_hall not in townhalls:
                    continue
                if roles and role_by_tag.get(m.tag) not in roles:
                    continue
            lines.append(f"• **{m.name}**, {remaining} left")
        return lines

    async def _mark_fired(self, pool, reminder_id, fire_key):
        await pool.execute(
            "INSERT INTO reminder_logs (reminder_id, fire_key) VALUES ($1, $2) ON CONFLICT DO NOTHING",
            reminder_id,
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
