"""/setup war-logs, post a clan's attack feed and war-phase embeds to a channel."""

from __future__ import annotations

import discord

from database import clans as clans_db
from database import warlogs as warlogs_db
from utils.embeds import error_embed, success_embed
from utils.tags import normalize_tag


async def handle(
    interaction: discord.Interaction,
    clan: str,
    channel: discord.TextChannel | None = None,
) -> None:
    await interaction.response.defer()
    tag = normalize_tag(clan)

    row = await clans_db.get_clan(interaction.guild_id, tag)
    if not row:
        await interaction.followup.send(
            embed=error_embed(f"`{tag}` is not an alliance clan. Add it first with `/alliance add-clan`.")
        )
        return

    target = channel or interaction.channel
    await warlogs_db.set_channel(interaction.guild_id, tag, target.id)
    await interaction.followup.send(
        embed=success_embed(
            f"War logs for **{row['name']}** (`{tag}`) → {target.mention}.\n"
            "Every war hit will be posted there, plus a war-info embed at prep, war start, "
            "the 18h/12h/6h marks, and war end."
        )
    )
