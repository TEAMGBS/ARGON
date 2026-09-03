"""Data access for clans that belong to a server's alliance.

A clan must be added to the server (via /alliance add-clan) before logs or
reminders can be set up for it. Clans are stored per guild in clan_stores.
"""

from __future__ import annotations

from database.db import get_pool


async def add_clan(guild_id: int, tag: str, name: str) -> None:
    pool = await get_pool()
    await pool.execute(
        """INSERT INTO clan_stores (guild_id, tag, name) VALUES ($1, $2, $3)
           ON CONFLICT (guild_id, tag) DO UPDATE SET name = EXCLUDED.name""",
        guild_id,
        tag,
        name,
    )


async def remove_clan(guild_id: int, tag: str) -> bool:
    """Remove a clan and everything configured for it. Returns True if it existed."""
    pool = await get_pool()
    result = await pool.execute("DELETE FROM clan_stores WHERE guild_id = $1 AND tag = $2", guild_id, tag)
    await pool.execute("DELETE FROM clan_logs WHERE guild_id = $1 AND tag = $2", guild_id, tag)
    await pool.execute("DELETE FROM clan_snapshots WHERE guild_id = $1 AND tag = $2", guild_id, tag)
    await pool.execute("DELETE FROM reminders WHERE guild_id = $1 AND clan_tag = $2", guild_id, tag)
    return not result.endswith("0")


async def get_clan(guild_id: int, tag: str):
    pool = await get_pool()
    return await pool.fetchrow("SELECT * FROM clan_stores WHERE guild_id = $1 AND tag = $2", guild_id, tag)


async def get_clans_for_guild(guild_id: int):
    pool = await get_pool()
    return await pool.fetch("SELECT * FROM clan_stores WHERE guild_id = $1 ORDER BY created_at", guild_id)
