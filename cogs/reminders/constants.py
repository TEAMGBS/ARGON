from __future__ import annotations

# Timing choices offered in the config UI: minutes before the event ends.
TIMING_CHOICES = [
    (15, "15m remaining"),
    (30, "30m remaining"),
    (45, "45m remaining"),
    (60, "1h remaining"),
    (90, "1h30m remaining"),
    (120, "2h remaining"),
    (180, "3h remaining"),
    (240, "4h remaining"),
    (360, "6h remaining"),
    (480, "8h remaining"),
    (600, "10h remaining"),
    (720, "12h remaining"),
    (900, "15h remaining"),
    (1080, "18h remaining"),
    (1200, "20h remaining"),
    (1440, "24h remaining"),
]

TOWNHALL_LEVELS = list(range(2, 19))

# Clan role values as returned by the Clash of Clans API.
CLAN_ROLES = ["leader", "coLeader", "elder", "member"]

ROLE_LABELS = {
    "leader": "Leader",
    "coLeader": "Co-Leader",
    "elder": "Elder",
    "member": "Member",
}

TYPE_LABELS = {
    "war": "Clan War Reminder",
    "capital": "Capital Raid Reminder",
    "cg": "Clan Games Reminder",
}
