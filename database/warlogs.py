"""Data access for per-clan war logs (attack feed + war-phase embeds)."""

from __future__ import annotations

from database.db import get_pool


async def set_channel(guild_id: int, tag: str, channel_id: int, war_type: str = "") -> None:
    pool = await get_pool()
    await pool.execute(
        """INSERT INTO war_logs (guild_id, tag, channel_id, war_type) VALUES ($1, $2, $3, $4)
           ON CONFLICT (guild_id, tag)
           DO UPDATE SET channel_id = EXCLUDED.channel_id, war_type = EXCLUDED.war_type""",
        guild_id,
        tag,
        channel_id,
        war_type,
    )


async def remove_channel(guild_id: int, tag: str) -> bool:
    pool = await get_pool()
    result = await pool.execute("DELETE FROM war_logs WHERE guild_id = $1 AND tag = $2", guild_id, tag)
    return not result.endswith("0")


async def all_tags() -> list[str]:
    pool = await get_pool()
    rows = await pool.fetch("SELECT DISTINCT tag FROM war_logs")
    return [row["tag"] for row in rows]


async def channels_for_tag(tag: str):
    pool = await get_pool()
    return await pool.fetch("SELECT guild_id, channel_id, war_type FROM war_logs WHERE tag = $1", tag)


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
