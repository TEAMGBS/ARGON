"""Read player units straight from the raw Clash of Clans API payload.

coc.py computes unit stats from bundled game-data tables and does
`self._static_data["levels"][level - start]`. When a unit's level exceeds those
tables — which happens after a game update adds levels the pinned coc.py doesn't
know yet — that raises `IndexError`. The client is created with
`raw_attribute=True`, so every player keeps its raw API dict, which already has
`name`, `level`, `maxLevel`, `village` (and `superTroopIsActive`) for each unit.
Reading from there avoids coc.py's game-data indexing entirely and stays correct
across future game updates.
"""


def home_units(player, key: str) -> list[dict]:
    """Home-village units of one kind from the raw payload.

    `key` is one of "heroes", "troops", "spells". Returns a list of dicts with
    at least `name`, `level` and `maxLevel`. Returns [] if raw data is missing.
    """
    raw = getattr(player, "_raw_data", None) or {}
    return [u for u in raw.get(key, []) if u.get("village") == "home"]


def active_super_troops(player) -> list[dict]:
    """Raw troop dicts for the player's currently-boosted Super Troops."""
    raw = getattr(player, "_raw_data", None) or {}
    return [u for u in raw.get("troops", []) if u.get("superTroopIsActive")]
