"""Data access for Legend League ranked tracking.

A guild sets a notification channel (ranked_settings) and adds players to track
(ranked_tracked). The poller keeps one trophy snapshot per tag (ranked_state)
and records every attack/defense it detects (ranked_events). Events are global
per player; notifications fan out to every guild tracking that player.
"""

from __future__ import annotations

from datetime import datetime

from database.db import get_pool


# ── Notification channel ──────────────────────────────────────────────────────
async def set_channel(guild_id: int, channel_id: int) -> None:
    pool = await get_pool()
    await pool.execute(
        """INSERT INTO ranked_settings (guild_id, channel_id, updated_at)
           VALUES ($1, $2, NOW())
           ON CONFLICT (guild_id) DO UPDATE SET channel_id = EXCLUDED.channel_id, updated_at = NOW()""",
        guild_id,
        channel_id,
    )


async def get_channel(guild_id: int):
    pool = await get_pool()
    return await pool.fetchval("SELECT channel_id FROM ranked_settings WHERE guild_id = $1", guild_id)


# ── Tracked players ───────────────────────────────────────────────────────────
async def add_tracked(guild_id: int, tag: str, name: str, added_by: int) -> None:
    pool = await get_pool()
    await pool.execute(
        """INSERT INTO ranked_tracked (guild_id, tag, name, added_by) VALUES ($1, $2, $3, $4)
           ON CONFLICT (guild_id, tag) DO UPDATE SET name = EXCLUDED.name""",
        guild_id,
        tag,
        name,
        added_by,
    )


async def remove_tracked(guild_id: int, tag: str) -> bool:
    pool = await get_pool()
    result = await pool.execute("DELETE FROM ranked_tracked WHERE guild_id = $1 AND tag = $2", guild_id, tag)
    return not result.endswith("0")


async def get_tracked_for_guild(guild_id: int):
    pool = await get_pool()
    return await pool.fetch("SELECT * FROM ranked_tracked WHERE guild_id = $1 ORDER BY created_at", guild_id)


async def all_tracked_tags() -> list[str]:
    """Every distinct tag tracked by any guild (what the poller iterates)."""
    pool = await get_pool()
    rows = await pool.fetch("SELECT DISTINCT tag FROM ranked_tracked")
    return [row["tag"] for row in rows]


async def guilds_tracking(tag: str):
    """(guild_id, channel_id) for each guild that tracks this tag and has a channel set."""
    pool = await get_pool()
    return await pool.fetch(
        """SELECT t.guild_id, s.channel_id
           FROM ranked_tracked t
           JOIN ranked_settings s ON s.guild_id = t.guild_id
           WHERE t.tag = $1""",
        tag,
    )


# ── Trophy snapshot state ─────────────────────────────────────────────────────
async def get_state(tag: str):
    pool = await get_pool()
    return await pool.fetchrow("SELECT * FROM ranked_state WHERE tag = $1", tag)


async def set_state(tag: str, name: str, trophies: int, season: str) -> None:
    pool = await get_pool()
    await pool.execute(
        """INSERT INTO ranked_state (tag, name, trophies, season, updated_at)
           VALUES ($1, $2, $3, $4, NOW())
           ON CONFLICT (tag) DO UPDATE
             SET name = EXCLUDED.name, trophies = EXCLUDED.trophies,
                 season = EXCLUDED.season, updated_at = NOW()""",
        tag,
        name,
        trophies,
        season,
    )


# ── Events ────────────────────────────────────────────────────────────────────
async def add_event(tag: str, season: str, direction: str, delta: int, trophies_after: int) -> None:
    pool = await get_pool()
    await pool.execute(
        """INSERT INTO ranked_events (tag, season, direction, delta, trophies_after)
           VALUES ($1, $2, $3, $4, $5)""",
        tag,
        season,
        direction,
        delta,
        trophies_after,
    )


async def events_since(tag: str, since: datetime):
    pool = await get_pool()
    return await pool.fetch(
        "SELECT * FROM ranked_events WHERE tag = $1 AND occurred_at >= $2 ORDER BY occurred_at",
        tag,
        since,
    )


async def events_for_season(tag: str, season: str):
    pool = await get_pool()
    return await pool.fetch(
        "SELECT * FROM ranked_events WHERE tag = $1 AND season = $2 ORDER BY occurred_at",
        tag,
        season,
    )


# ── Autocomplete source ───────────────────────────────────────────────────────
async def known_tags(query: str, limit: int = 25):
    """Tags the bot has seen before (tracked, linked, or previously polled),
    for the player-tag autocomplete. Returns rows of (tag, name)."""
    pool = await get_pool()
    rows = await pool.fetch(
        """SELECT tag, MAX(name) AS name FROM (
               SELECT tag, name FROM ranked_tracked
               UNION ALL SELECT tag, name FROM ranked_state
               UNION ALL SELECT tag, name FROM linked_accounts
           ) all_tags
           WHERE tag IS NOT NULL AND ($1 = '' OR tag ILIKE '%' || $1 || '%' OR name ILIKE '%' || $1 || '%')
           GROUP BY tag
           ORDER BY name
           LIMIT $2""",
        query or "",
        limit,
    )
    return rows
