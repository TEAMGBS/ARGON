from __future__ import annotations

# Reminder times are entered on the /reminders create command itself (see
# duration.py), so there is no longer a timing select in the config UI.

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

# War types a war reminder can be limited to. Empty selection = every war type.
WAR_TYPES = [
    ("normal", "Normal War"),
    ("cwl", "CWL"),
    ("friendly", "Friendly"),
]

WAR_TYPE_LABELS = {value: label for value, label in WAR_TYPES}
