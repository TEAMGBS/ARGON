"""/emoji categorize, file existing emojis into a category by a name match.

Handy for categorizing emojis that were uploaded before categories existed, e.g.
`/emoji categorize category:CWL match:cwl` or `match:TH` for Town Halls.
"""

from __future__ import annotations

import discord

from database import emojis as emojis_db
from utils.embeds import error_embed

from ..categories import normalize_category


async def handle(interaction: discord.Interaction, category: str, match: str | None = None) -> None:
    await interaction.response.defer(ephemeral=True, thinking=True)

    if not await interaction.client.is_owner(interaction.user):
        await interaction.followup.send(
            embed=error_embed("Only the bot owner can manage application emojis."), ephemeral=True
        )
        return

    cat = normalize_category(category)
    if not cat:
        await interaction.followup.send(embed=error_embed("Give a category name."), ephemeral=True)
        return

    needle = (match or "").lower()
    emojis = await interaction.client.fetch_application_emojis()
    targets = [e for e in emojis if not needle or needle in e.name.lower()]
    if not targets:
        await interaction.followup.send(
            embed=error_embed(f"No emojis match `{match}`." if match else "This bot has no emojis."), ephemeral=True
        )
        return

    for e in targets:
        await emojis_db.set_category(e.name, cat)

    where = f" matching `{match}`" if match else ""
    names = ", ".join(e.name for e in targets)
    await interaction.followup.send(
        f"**Categorized {len(targets)}** emoji(s){where} → _{cat}_.\n{names[:1800]}", ephemeral=True
    )
