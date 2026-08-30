"""Small formatting helpers shared across cogs."""

from datetime import datetime, timezone


def discord_relative(dt: datetime) -> str:
    """A Discord relative timestamp, e.g. <t:1700000000:R> ("in 3 hours")."""
    return f"<t:{int(dt.replace(tzinfo=dt.tzinfo or timezone.utc).timestamp())}:R>"


def discord_short(dt: datetime) -> str:
    """A Discord short date-time timestamp, e.g. <t:...:f>."""
    return f"<t:{int(dt.replace(tzinfo=dt.tzinfo or timezone.utc).timestamp())}:f>"


def humanize_seconds(seconds: float) -> str:
    """Turn a number of seconds into e.g. '2d 3h 10m'."""
    seconds = int(max(0, seconds))
    days, rem = divmod(seconds, 86400)
    hours, rem = divmod(rem, 3600)
    minutes = rem // 60
    parts = []
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    if minutes or not parts:
        parts.append(f"{minutes}m")
    return " ".join(parts)


def pad(value, width: int) -> str:
    """Left-align within a fixed width for monospace tables (truncates if longer)."""
    s = str(value)
    return s[:width] if len(s) >= width else s + " " * (width - len(s))


def pad_start(value, width: int) -> str:
    """Right-align a value within a fixed width."""
    return str(value).rjust(width)


def chunk(items, size: int):
    """Yield successive ``size``-length chunks from ``items``."""
    for i in range(0, len(items), size):
        yield items[i : i + size]
