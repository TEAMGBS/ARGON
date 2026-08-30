"""Postgres (Supabase) connection pool.

A single global asyncpg pool is created at startup and shared by every cog.
`schema.sql` is applied in full on connect and is written with `IF NOT EXISTS`,
so a brand-new Supabase database is fully built from that one file and re-running
it against an existing database is harmless.
"""

import os

import asyncpg

from config import DATABASE_URL

_pool: asyncpg.Pool | None = None

SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema.sql")


async def init_pool() -> asyncpg.Pool:
    """Create the global connection pool and apply the schema (idempotent)."""
    global _pool

    # Supabase's transaction pooler (port 6543) runs pgbouncer, which does not
    # support prepared statements, asyncpg uses them by default, so we disable
    # its statement cache. This is a no-op against a direct connection too.
    _pool = await asyncpg.create_pool(
        dsn=DATABASE_URL,
        min_size=1,
        max_size=10,
        statement_cache_size=0,
    )

    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema = f.read()

    async with _pool.acquire() as conn:
        await conn.execute(schema)

    return _pool


async def get_pool() -> asyncpg.Pool:
    """Return the initialized pool. Raises if init_pool() hasn't run yet."""
    if _pool is None:
        raise RuntimeError("Database pool not initialized. Call init_pool() first.")
    return _pool


async def close_pool() -> None:
    """Close the pool on shutdown."""
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None
