"""Background scheduler: fires due war reminders and posts clan feed logs.

This is the Python equivalent of ClashPerk's feed/reminder pipeline, kept simple
and self-contained: a single loop polls each linked clan and each configured
reminder. It runs inside the reminders cog and starts once the bot is ready.
"""

import json
import traceback

import coc
import discord
from discord.ext import commands, tasks

from config import POLL_INTERVAL_SECONDS
from database.db import get_pool
from utils.embeds import guild_color
from utils.emojis import E_DONATE, E_RECEIVE, E_UP, E_DOWN, E_CLAN, get_th_emoji
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
        # get_current_war covers every war type: regular, friendly, and (auto
        # detected) CWL league wars, with attacks_per_member adapting (2 for
        # regular/friendly, 1 for CWL). The only unreadable case is a regular war
        # whose war log is private - the API hides the attack data (403), so we
        # log it and move on.
        tag = r["clan_tag"]
        try:
            war = await self.bot.coc_client.get_current_war(tag)
        except coc.PrivateWarLog:
            print(f"[reminder {r['id']}] {tag}: war log is private, cannot read attacks. Ask the clan to make it public.")
            return
        except coc.Maintenance:
            print(f"[reminder {r['id']}] {tag}: Clash of Clans API is in maintenance; retrying next tick.")
            return
        except coc.NotFound:
            print(f"[reminder {r['id']}] {tag}: clan not found (bad tag?).")
            return
        except Exception:
            print(f"[reminder {r['id']}] {tag}: failed to fetch current war:\n{traceback.format_exc()}")
            return

        if war is None or war.state != "inWar":
            return

        # Only fire for the war types this reminder is limited to (empty = all).
        selected_types = set(r["war_types"] or [])
        if selected_types and self._war_type(war) not in selected_types:
            return

        minutes_left = war.end_time.seconds_until / 60
        timings = r["timing_minutes"] or []
        if not timings:
            print(f"[reminder {r['id']}] {tag}: inWar with {minutes_left:.0f}m left but no timings set; nothing to fire.")
            return
        # Only log while the war is within reach of a timing, so idle early-war
        # polls stay quiet but the "not due yet" reason is visible near firing.
        if minutes_left <= max(timings) + 5:
            print(f"[reminder {r['id']}] {tag}: inWar, {minutes_left:.0f}m left, timings={timings}, war_type={self._war_type(war)}.")

        # How late we're still willing to deliver a timing we missed (poll jitter,
        # a slow API call, or a brief restart). Beyond this the timing is recorded
        # as fired without sending, so a long outage doesn't spam stale reminders.
        catchup = max(30.0, poll_minutes * 5)
        for timing in (r["timing_minutes"] or []):
            # Fire once the war has crossed below this timing threshold - not only
            # inside a one-minute window, so a delayed poll never drops it.
            if minutes_left > timing:
                continue

            fire_key = f"{war.end_time.raw_time}:{timing}"
            exists = await pool.fetchval(
                "SELECT 1 FROM reminder_logs WHERE reminder_id = $1 AND fire_key = $2", r["id"], fire_key
            )
            if exists:
                continue

            # We're well past the intended time (e.g. the bot was down for a while):
            # mark it handled but don't send a confusing late reminder.
            if minutes_left < timing - catchup:
                await self._mark_fired(pool, r["id"], fire_key)
                continue

            laggards = await self._war_laggards(r, war)
            if not laggards:
                # Still record the fire so we don't re-check this window every tick.
                await self._mark_fired(pool, r["id"], fire_key)
                continue

            content = await self._build_war_message(pool, r, war, laggards)
            sent = await self._send_text(r["guild_id"], r["channel_id"], content)
            if sent:
                print(
                    f"[reminder {r['id']}] {tag}: sent {timing}m war reminder for {war.clan.name} "
                    f"to {len(laggards)} member(s) in channel {r['channel_id']}."
                )
            await self._mark_fired(pool, r["id"], fire_key)

    @staticmethod
    def _war_type(war) -> str:
        """Classify the current war as 'cwl', 'friendly', or 'normal'."""
        if getattr(war, "is_cwl", False):
            return "cwl"
        return "friendly" if getattr(war, "type", None) == "friendly" else "normal"

    async def _war_laggards(self, r, war) -> list[dict]:
        """War members who still owe attacks, after the reminder's filters.

        Each entry: {tag, name, th, used, total}. The caller turns these into
        the message lines (with a Town Hall emoji and a ping for linked users).
        """
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

        members = []
        for m in war.clan.members:
            used = len(m.attacks)
            remaining = per_member - used
            if remaining <= 0:
                continue
            if remaining_filter and remaining not in remaining_filter:
                continue
            if filtered:
                if townhalls and m.town_hall not in townhalls:
                    continue
                if roles and role_by_tag.get(m.tag) not in roles:
                    continue
            members.append({"tag": m.tag, "name": m.name, "th": m.town_hall, "used": used, "total": per_member})
        return members

    async def _build_war_message(self, pool, r, war, laggards) -> str:
        """ClashPerk-style war reminder: a bell header, the optional message, then
        one line per member as `{TH emoji} {@mention or name} ({used}/{total})`.
        Linked members are pinged and listed first, unlinked members follow."""
        # Which of these players are linked to a Discord account (to @mention them).
        tags = [m["tag"] for m in laggards]
        link_rows = await pool.fetch("SELECT tag, discord_id FROM linked_accounts WHERE tag = ANY($1)", tags)
        link_map = {row["tag"]: row["discord_id"] for row in link_rows}

        def line(m: dict, discord_id) -> str:
            th = get_th_emoji(m["th"])
            # Name + attack count go inside a code span; a leading backtick in a
            # name would break it, so drop any backticks. The TH emoji and the
            # ping stay outside (custom emoji and mentions don't work in code).
            name = m["name"].replace("`", "")
            code = f"`{name} ({m['used']}/{m['total']})`"
            return f"{th} {code} <@{discord_id}>" if discord_id else f"{th} {code}"

        linked = [line(m, link_map[m["tag"]]) for m in laggards if m["tag"] in link_map]
        unlinked = [line(m, None) for m in laggards if m["tag"] not in link_map]

        parts = [f"**{war.clan.name} (War ends {discord_relative(war.end_time.time)})**"]
        if r["message"]:
            parts.append(f"{r['message']}")
        parts.append("")

        body = linked[:40]
        if linked and unlinked:
            body.append("")
        body += unlinked[: max(0, 40 - len(linked))]

        return "\n".join(parts + body)[:2000]

    async def _mark_fired(self, pool, reminder_id, fire_key):
        await pool.execute(
            "INSERT INTO reminder_logs (reminder_id, fire_key) VALUES ($1, $2) ON CONFLICT DO NOTHING",
            reminder_id,
            fire_key,
        )

    # ── Helpers ───────────────────────────────────────────────────────────────
    async def _send_text(self, guild_id, channel_id, content: str) -> bool:
        """Send a plain-content message; returns True on success. Mentions only
        notify from message content (not from inside an embed), so war reminders
        use this to actually ping. Failures are logged so the reason shows up in
        the Railway logs instead of vanishing."""
        channel = self.bot.get_channel(int(channel_id))
        if channel is None:
            try:
                channel = await self.bot.fetch_channel(int(channel_id))
            except discord.Forbidden:
                print(f"[reminder] channel {channel_id} (guild {guild_id}): no access (bot not in server or missing View Channel).")
                return False
            except discord.NotFound:
                print(f"[reminder] channel {channel_id} (guild {guild_id}): channel no longer exists.")
                return False
            except Exception as exc:
                print(f"[reminder] channel {channel_id} (guild {guild_id}): could not fetch: {exc!r}")
                return False
        if not isinstance(channel, discord.abc.Messageable):
            print(f"[reminder] channel {channel_id} (guild {guild_id}): not a text channel ({type(channel).__name__}).")
            return False
        try:
            await channel.send(
                content=content[:2000],
                allowed_mentions=discord.AllowedMentions(users=True, roles=False, everyone=False),
            )
            return True
        except discord.Forbidden:
            print(f"[reminder] channel {channel_id} (guild {guild_id}): missing permission to send (need Send Messages).")
        except discord.HTTPException as exc:
            print(f"[reminder] channel {channel_id} (guild {guild_id}): Discord rejected the message: {exc!r}")
        except Exception as exc:
            print(f"[reminder] channel {channel_id} (guild {guild_id}): failed to send: {exc!r}")
        return False

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
