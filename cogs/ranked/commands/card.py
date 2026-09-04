"""/ranked card-player, render the legend battle-log card for any player.

Works for any tag. If the player is tracked, the card shows this season's
recorded attacks/defenses; otherwise it shows the header stats from the API with
an empty grid (we never polled them, so there are no per-attack tiles).
"""

from __future__ import annotations

import io

import discord

from database import ranked as ranked_db
from utils.embeds import error_embed, format_tag
from utils.tags import is_valid_tag

from ..render import render_card
from ..season import season_key


async def handle(interaction: discord.Interaction, tag: str) -> None:
    if not is_valid_tag(tag):
        await interaction.response.send_message(embed=error_embed("That is not a valid player tag."), ephemeral=True)
        return

    await interaction.response.defer()
    tag = format_tag(tag)
    try:
        player = await interaction.client.coc_client.get_player(tag)
    except Exception:
        await interaction.followup.send(embed=error_embed(f"No player found for `{tag}`."))
        return

    events = await ranked_db.events_for_season(tag, season_key())

    rank = None
    stats = getattr(player, "legend_statistics", None)
    current = getattr(stats, "current_season", None) if stats else None
    if current is not None:
        rank = getattr(current, "rank", None)

    try:
        png = render_card(
            name=player.name,
            tag=tag,
            rank=rank,
            trophies=player.trophies,
            events=[{"direction": e["direction"], "delta": e["delta"]} for e in events],
        )
    except ImportError:
        await interaction.followup.send(
            embed=error_embed("The image library isn't available on the bot right now.")
        )
        return

    content = None
    if not events:
        content = (
            "_No recorded legend attacks this season for this player. "
            "Track them with `/ranked track-player` to start recording._"
        )
    await interaction.followup.send(content=content, file=discord.File(io.BytesIO(png), filename="legend.png"))
