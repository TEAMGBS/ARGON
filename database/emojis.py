"""Data access for application-emoji categories (bot-global)."""

from __future__ import annotations

from database.db import get_pool


async def set_category(name: str, category: str) -> None:
    pool = await get_pool()
    await pool.execute(
        """INSERT INTO emoji_categories (name, category, updated_at) VALUES ($1, $2, NOW())
           ON CONFLICT (name) DO UPDATE SET category = EXCLUDED.category, updated_at = NOW()""",
        name,
        category,
    )


async def mapping() -> dict[str, str]:
    """name -> category for every categorized emoji."""
    pool = await get_pool()
    rows = await pool.fetch("SELECT name, category FROM emoji_categories")
    return {row["name"]: row["category"] for row in rows}


async def categories() -> list[str]:
    """Distinct categories in use, alphabetically."""
    pool = await get_pool()
    rows = await pool.fetch("SELECT DISTINCT category FROM emoji_categories ORDER BY category")
    return [row["category"] for row in rows]
