"""Clash of Clans tag helpers, shared so every command handles tags the same way."""

import re

_TAG_RE = re.compile(r"^#[0-9A-Z]{3,12}$")


def normalize_tag(raw: str) -> str:
    """Uppercase a CoC tag, turn the letter ``O`` into ``0`` (CoC tags never
    contain the letter O), strip anything that isn't a tag character, and ensure a
    single leading ``#``."""
    cleaned = (raw or "").strip().upper().replace("O", "0")
    cleaned = re.sub(r"[^0-9A-Z]", "", cleaned)
    return "#" + cleaned


def is_valid_tag(raw: str) -> bool:
    """True if the value looks like a valid CoC tag once normalized."""
    return bool(_TAG_RE.match(normalize_tag(raw)))
