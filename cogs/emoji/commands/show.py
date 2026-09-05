"""/emoji show, list the bot's application emojis grouped by category.

Default view renders each emoji next to its name, under a header per category.
Pass ``raw: True`` for copy-paste lines for the CUSTOM map in utils/emojis.py,
or ``category:`` to show only one category.
"""

from __future__ import annotations

import discord

from database import emojis as emojis_db
from utils.embeds import error_embed

from ..categories import UNCATEGORIZED, normalize_category


def _chunk_messages(lines: list[str], limit: int = 1900) -> list[str]:
    pages, current = [], ""
    for line in lines:
        if len(current) + len(line) + 1 > limit:
            if current:
                pages.append(current)
            current = line
        else:
            current = f"{current}\n{line}" if current else line
    if current:
        pages.append(current)
    return pages


def _group(emojis, mapping):
    """{category: [emoji, ...]} with Uncategorized last."""
    groups: dict[str, list] = {}
    for e in emojis:
        groups.setdefault(mapping.get(e.name, UNCATEGORIZED), []).append(e)
    ordered = sorted((c for c in groups if c != UNCATEGORIZED), key=str.lower)
    if UNCATEGORIZED in groups:
        ordered.append(UNCATEGORIZED)
    return [(c, sorted(groups[c], key=lambda e: e.name.lower())) for c in ordered]


async def handle(interaction: discord.Interaction, raw: bool = False, category: str | None = None) -> None:
    # Acknowledge immediately - the owner check does an HTTP fetch and would
    # otherwise blow the 3s response window (error 10062: Unknown interaction).
    await interaction.response.defer(ephemeral=True, thinking=True)

    if not await interaction.client.is_owner(interaction.user):
        await interaction.followup.send(
            embed=error_embed("Only the bot owner can view application emojis."), ephemeral=True
        )
        return

    emojis = await interaction.client.fetch_application_emojis()
    if not emojis:
        await interaction.followup.send("This bot has no application emojis yet. Add some with `/emoji add`.", ephemeral=True)
        return

    mapping = await emojis_db.mapping()
    grouped = _group(emojis, mapping)

    wanted = normalize_category(category)
    if wanted:
        grouped = [(c, es) for c, es in grouped if c.lower() == wanted.lower()]
        if not grouped:
            await interaction.followup.send(
                embed=error_embed(f"No emojis in category **{wanted}**."), ephemeral=True
            )
            return

    if raw:
        # Copy-paste-ready for the CUSTOM dict in utils/emojis.py, grouped by a
        # `# Category` comment.
        body: list[str] = []
        for cat, es in grouped:
            body.append(f"    # {cat}")
            body += [f'    "{e.name}": "<{"a" if e.animated else ""}:{e.name}:{e.id}>",' for e in es]
        for i, page in enumerate(_chunk_messages(body, limit=1850)):
            header = f"**{len(emojis)} application emoji(s)** · raw ({i + 1})\n" if i == 0 else ""
            await interaction.followup.send(f"{header}```py\n{page}\n```", ephemeral=True)
        return

    lines: list[str] = []
    for cat, es in grouped:
        lines.append(f"\n__**{cat}**__ ({len(es)})")
        lines += [f"{e} `{e.name}` · `{e.id}`" for e in es]
    for i, page in enumerate(_chunk_messages(lines)):
        header = f"**{len(emojis)} application emoji(s)**\n" if i == 0 else ""
        await interaction.followup.send(f"{header}{page}"[:2000], ephemeral=True)
