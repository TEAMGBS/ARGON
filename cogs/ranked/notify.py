"""Build the legend attack/defense notification posted to the tracking channel.

Only data the official API exposes is used: the trophy change, the running
total, and week offense/defense tallies computed from our recorded events.
Opponent, stars, destruction % and army are not available from the public API.
"""

from __future__ import annotations

from database import ranked as ranked_db

from .season import week_start


async def build_notification(tag: str, name: str, direction: str, delta: int, trophies_after: int) -> str:
    events = await ranked_db.events_since(tag, week_start())
    off_troph = sum(e["delta"] for e in events if e["direction"] == "attack")
    off_count = sum(1 for e in events if e["direction"] == "attack")
    def_troph = sum(-e["delta"] for e in events if e["direction"] == "defense")  # magnitude
    def_count = sum(1 for e in events if e["direction"] == "defense")

    marker = "⚔️" if direction == "attack" else "🛡️"
    word = "Offense" if direction == "attack" else "Defense"
    sign = f"+{delta}" if delta >= 0 else str(delta)

    return "\n".join(
        [
            f"{marker} **{word}** • **{name}**",
            f"{sign} → {trophies_after} 🏆",
            f"⚔️ Week Off: +{off_troph}/{off_count}   🛡️ Week Def: -{def_troph}/{def_count}",
            f"Player Tag: `{tag}`",
        ]
    )
