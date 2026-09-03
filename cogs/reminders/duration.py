"""Parse and format reminder times typed into the /reminders create command.

Accepts free-form durations like ``2h2m``, ``1h``, ``30m``, a bare number of
minutes like ``90``, and several of them at once separated by commas, e.g.
``1h, 30m``. Also provides the autocomplete that suggests common presets while
still letting the user type any value.
"""

from __future__ import annotations

import re

from discord import app_commands

_MAX_MINUTES = 2880  # 48h - the hard cap; nothing longer is accepted.

# Common presets offered by the autocomplete (minutes).
_PRESETS = [15, 30, 45, 60, 90, 120, 180, 240, 360, 480, 600, 720, 1440, 2880]

_HM_RE = re.compile(r"^(?:(\d+)h)?(?:(\d+)m)?$")


class DurationError(ValueError):
    """Raised with a user-facing message when a time can't be parsed."""


def format_minutes(total: int) -> str:
    """Minutes to a short token, e.g. 122 -> '2h2m', 90 -> '1h30m', 30 -> '30m'."""
    hours, minutes = divmod(int(total), 60)
    if hours and minutes:
        return f"{hours}h{minutes}m"
    if hours:
        return f"{hours}h"
    return f"{minutes}m"


def _parse_one(part: str) -> int | None:
    """One duration token to minutes. Raises DurationError with a clear message."""
    token = part.strip()
    if not token:
        return None
    compact = token.lower().replace(" ", "")
    if compact.isdigit():
        minutes = int(compact)
    else:
        match = _HM_RE.fullmatch(compact)
        if not match or (match.group(1) is None and match.group(2) is None):
            raise DurationError(f"`{token}` is not a valid time. Try `1h`, `30m`, or `2h30m`.")
        minutes = int(match.group(1) or 0) * 60 + int(match.group(2) or 0)
    if minutes < 1:
        raise DurationError(f"`{token}` must be at least 1 minute.")
    if minutes > _MAX_MINUTES:
        raise DurationError("The longest reminder time is 48h; you can't set more than that.")
    return minutes


def parse_durations(text: str) -> list[int]:
    """Parse one or more comma/newline separated durations into sorted minutes.

    Raises ValueError(bad_token) naming the first token that could not be parsed.
    """
    if not text:
        return []
    values = []
    for part in re.split(r"[,\n]", text):
        minutes = _parse_one(part)
        if minutes is not None:
            values.append(minutes)
    return sorted(set(values))


async def time_autocomplete(interaction, current: str) -> list[app_commands.Choice]:
    """Suggest preset times while still accepting free-form input like '2h30m'."""
    current = (current or "").strip()
    choices: list[app_commands.Choice] = []
    seen: set[str] = set()

    # Echo the typed value first when it parses, so it is pickable as-is.
    if current:
        try:
            parsed = parse_durations(current)
        except ValueError:
            parsed = []
        if parsed:
            label = ", ".join(format_minutes(m) for m in parsed)
            choices.append(app_commands.Choice(name=label[:100], value=current[:100]))
            seen.add(label)

    for minutes in _PRESETS:
        token = format_minutes(minutes)
        if token in seen:
            continue
        if not current or current.lower() in token:
            choices.append(app_commands.Choice(name=token, value=token))
            seen.add(token)

    return choices[:25]
