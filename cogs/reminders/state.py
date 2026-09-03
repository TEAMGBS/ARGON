from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ReminderState:
    """Working state for the reminder config UI. Loaded from an existing reminder
    when editing, or built fresh when creating one."""

    reminder_id: str | None
    guild_id: int
    clan_tag: str
    clan_name: str
    type: str
    channel_id: int
    created_by: int
    message: str = ""
    timing_minutes: list[int] = field(default_factory=list)
    threshold: int = 0
    remaining_filter: list[int] = field(default_factory=list)
    member_scope: str = "all"
    townhalls: list[int] = field(default_factory=list)
    roles: list[str] = field(default_factory=list)
    war_types: list[str] = field(default_factory=list)

    @classmethod
    def from_row(cls, row, clan_name: str) -> "ReminderState":
        return cls(
            reminder_id=row["id"],
            guild_id=row["guild_id"],
            clan_tag=row["clan_tag"],
            clan_name=clan_name,
            type=row["type"],
            channel_id=row["channel_id"],
            created_by=row["created_by"],
            message=row["message"] or "",
            timing_minutes=list(row["timing_minutes"] or []),
            threshold=row["threshold"],
            remaining_filter=list(row["remaining_filter"] or []),
            member_scope=row["member_scope"],
            townhalls=list(row["townhalls"] or []),
            roles=list(row["roles"] or []),
            war_types=list(row["war_types"] or []),
        )
