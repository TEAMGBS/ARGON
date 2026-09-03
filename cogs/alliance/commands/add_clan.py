"""/alliance add-clan, add a clan to this server so logs and reminders can be set up for it."""

from __future__ import annotations

import discord

from database import clans as clans_db
from utils.embeds import error_embed, format_tag, success_embed
from utils.tags import is_valid_tag


async def handle(interaction: discord.Interaction, tag: str) -> None:
    if not is_valid_tag(tag):
        await interaction.response.send_message(embed=error_embed("That is not a valid clan tag."), ephemeral=True)
        return

    await interaction.response.defer()
    tag = format_tag(tag)

    try:
        clan = await interaction.client.coc_client.get_clan(tag)
    except Exception:
        await interaction.followup.send(embed=error_embed(f"No clan found for `{tag}`."))
        return

    await clans_db.add_clan(interaction.guild_id, tag, clan.name)
    await interaction.followup.send(
        embed=success_embed(
            f"Added **{clan.name}** (`{tag}`) to this server. You can now set up logs and reminders for it."
        )
    )
