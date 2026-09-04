"""Legend League time helpers: season key, legend-day start, and week start.

Clash of Clans resets the trophy season on the last Monday of the month at
05:00 UTC, and the legend "day" rolls over daily at 05:00 UTC.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import coc

RESET_HOUR = 5  # 05:00 UTC


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def season_key(now: datetime | None = None) -> str:
    """A stable key for the current trophy season, e.g. '2026-09'."""
    try:
        start = coc.utils.get_season_start()
        if start is not None:
            return start.strftime("%Y-%m")
    except Exception:
        pass
    return (now or now_utc()).strftime("%Y-%m")


def legend_day_start(now: datetime | None = None) -> datetime:
    """Start of the current legend day (most recent 05:00 UTC)."""
    now = now or now_utc()
    reset = now.replace(hour=RESET_HOUR, minute=0, second=0, microsecond=0)
    if now < reset:
        reset -= timedelta(days=1)
    return reset


def week_start(now: datetime | None = None) -> datetime:
    """Start of a rolling 7-day window ending now (used for 'Week Off/Def')."""
    return (now or now_utc()) - timedelta(days=7)
