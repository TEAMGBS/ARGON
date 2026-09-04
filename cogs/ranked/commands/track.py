"""/ranked track-player, start tracking a player's legend attacks/defenses."""

from __future__ import annotations

import discord

from database import ranked as ranked_db
from utils.embeds import error_embed, format_tag, success_embed
from utils.tags import is_valid_tag

from ..season import season_key
from ._guard import require_manage


async def handle(interaction: discord.Interaction, tag: str) -> None:
    if not await require_manage(interaction):
        return
    if not is_valid_tag(tag):
        await interaction.response.send_message(embed=error_embed("That is not a valid player tag."), ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)
    tag = format_tag(tag)
    try:
        player = await interaction.client.coc_client.get_player(tag)
    except Exception:
        await interaction.followup.send(embed=error_embed(f"No player found for `{tag}`."), ephemeral=True)
        return

    await ranked_db.add_tracked(interaction.guild_id, tag, player.name, interaction.user.id)
    # Seed the baseline so the first poll doesn't emit a bogus event, and so we
    # only record attacks from now on (no back-fill of past attacks).
    if await ranked_db.get_state(tag) is None:
        await ranked_db.set_state(tag, player.name, player.trophies, season_key())

    await interaction.followup.send(
        embed=success_embed(
            f"Now tracking **{player.name}** (`{tag}`). Attacks and defenses will be recorded from now on."
        ),
        ephemeral=True,
    )
