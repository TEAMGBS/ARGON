"""Data access for per-clan war logs (attack feed + war-phase embeds)."""

from __future__ import annotations

import random
import string

from database.db import get_pool

_ID_ALPHABET = string.ascii_uppercase + string.digits


async def _generate_id(conn) -> str:
    for _ in range(25):
        candidate = "".join(random.choices(_ID_ALPHABET, k=6))
        if not await conn.fetchval("SELECT 1 FROM war_logs WHERE id = $1", candidate):
            return candidate
    raise RuntimeError("Could not generate a unique war-log id")


_DEFAULT_TIMINGS = [1080, 720, 360]  # 18h / 12h / 6h left


async def set_channel(
    guild_id: int, tag: str, channel_id: int, war_type: str = "", timings: list[int] | None = None
) -> str:
    """Create or update a clan's war log. Returns its id (kept stable on update)."""
    timings = timings if timings is not None else _DEFAULT_TIMINGS
    pool = await get_pool()
    async with pool.acquire() as conn:
        existing = await conn.fetchval("SELECT id FROM war_logs WHERE guild_id = $1 AND tag = $2", guild_id, tag)
        if existing:
            await conn.execute(
                "UPDATE war_logs SET channel_id = $3, war_type = $4, timings = $5 WHERE guild_id = $1 AND tag = $2",
                guild_id,
                tag,
                channel_id,
                war_type,
                timings,
            )
            return existing
        new_id = await _generate_id(conn)
        await conn.execute(
            "INSERT INTO war_logs (id, guild_id, tag, channel_id, war_type, timings) VALUES ($1, $2, $3, $4, $5, $6)",
            new_id,
            guild_id,
            tag,
            channel_id,
            war_type,
            timings,
        )
        return new_id


async def remove_by_id(guild_id: int, log_id: str) -> bool:
    pool = await get_pool()
    result = await pool.execute("DELETE FROM war_logs WHERE guild_id = $1 AND id = $2", guild_id, log_id)
    return not result.endswith("0")


async def get_by_id(guild_id: int, log_id: str):
    pool = await get_pool()
    return await pool.fetchrow("SELECT * FROM war_logs WHERE guild_id = $1 AND id = $2", guild_id, log_id)


async def list_for_guild(guild_id: int):
    """War logs for a guild with the clan name joined in (for /setup and autocomplete)."""
    pool = await get_pool()
    return await pool.fetch(
        """SELECT w.id, w.tag, w.channel_id, w.war_type, w.timings, c.name
           FROM war_logs w
           LEFT JOIN clan_stores c ON c.guild_id = w.guild_id AND c.tag = w.tag
           WHERE w.guild_id = $1
           ORDER BY w.created_at""",
        guild_id,
    )


async def all_tags() -> list[str]:
    pool = await get_pool()
    rows = await pool.fetch("SELECT DISTINCT tag FROM war_logs")
    return [row["tag"] for row in rows]


async def channels_for_tag(tag: str):
    pool = await get_pool()
    return await pool.fetch("SELECT guild_id, channel_id, war_type, timings FROM war_logs WHERE tag = $1", tag)


async def get_progress(guild_id: int, tag: str, war_key: str):
    pool = await get_pool()
    return await pool.fetchrow(
        "SELECT last_order, events FROM war_log_progress WHERE guild_id = $1 AND tag = $2 AND war_key = $3",
        guild_id,
        tag,
        war_key,
    )


async def set_progress(guild_id: int, tag: str, war_key: str, last_order: int, events: list[str]) -> None:
    pool = await get_pool()
    await pool.execute(
        """INSERT INTO war_log_progress (guild_id, tag, war_key, last_order, events, updated_at)
           VALUES ($1, $2, $3, $4, $5, NOW())
           ON CONFLICT (guild_id, tag, war_key)
           DO UPDATE SET last_order = EXCLUDED.last_order, events = EXCLUDED.events, updated_at = NOW()""",
        guild_id,
        tag,
        war_key,
        last_order,
        events,
    )
