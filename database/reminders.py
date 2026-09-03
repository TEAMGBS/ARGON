"""Data access for reminders.

Each reminder has a short string id (easy to type in /reminders delete), a type
(war / capital / cg), a set of timing choices (minutes before the event ends), and
optional member filters. asyncpg maps Postgres arrays to/from Python lists.
"""

from __future__ import annotations

import random
import string

from database.db import get_pool

_ID_ALPHABET = string.ascii_uppercase + string.digits


async def _generate_id(conn) -> str:
    for _ in range(25):
        candidate = "".join(random.choices(_ID_ALPHABET, k=6))
        exists = await conn.fetchval("SELECT 1 FROM reminders WHERE id = $1", candidate)
        if not exists:
            return candidate
    raise RuntimeError("Could not generate a unique reminder id")


async def create_reminder(
    *,
    guild_id: int,
    clan_tag: str,
    type_: str,
    channel_id: int,
    created_by: int,
    message: str,
) -> str:
    pool = await get_pool()
    async with pool.acquire() as conn:
        reminder_id = await _generate_id(conn)
        await conn.execute(
            """INSERT INTO reminders (id, guild_id, clan_tag, type, channel_id, created_by, message)
               VALUES ($1, $2, $3, $4, $5, $6, $7)""",
            reminder_id,
            guild_id,
            clan_tag,
            type_,
            channel_id,
            created_by,
            message,
        )
    return reminder_id


async def update_reminder(
    reminder_id: str,
    *,
    message: str,
    channel_id: int,
    timing_minutes: list[int],
    threshold: int,
    remaining_filter: list[int],
    member_scope: str,
    townhalls: list[int],
    roles: list[str],
    war_types: list[str],
) -> None:
    pool = await get_pool()
    await pool.execute(
        """UPDATE reminders SET
               message = $2,
               channel_id = $3,
               timing_minutes = $4,
               threshold = $5,
               remaining_filter = $6,
               member_scope = $7,
               townhalls = $8,
               roles = $9,
               war_types = $10
           WHERE id = $1""",
        reminder_id,
        message,
        channel_id,
        timing_minutes,
        threshold,
        remaining_filter,
        member_scope,
        townhalls,
        roles,
        war_types,
    )


async def get_reminder(reminder_id: str):
    pool = await get_pool()
    return await pool.fetchrow("SELECT * FROM reminders WHERE id = $1", reminder_id)


async def delete_reminder(reminder_id: str) -> None:
    pool = await get_pool()
    await pool.execute("DELETE FROM reminders WHERE id = $1", reminder_id)
    await pool.execute("DELETE FROM reminder_logs WHERE reminder_id = $1", reminder_id)


async def get_reminders_for_guild(guild_id: int):
    pool = await get_pool()
    return await pool.fetch("SELECT * FROM reminders WHERE guild_id = $1 ORDER BY created_at", guild_id)


async def get_all_reminders():
    """Every reminder across all guilds, used by the scheduler."""
    pool = await get_pool()
    return await pool.fetch("SELECT * FROM reminders")
