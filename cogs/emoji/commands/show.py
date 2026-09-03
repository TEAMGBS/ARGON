"""/emoji show, list every application emoji the bot owns.

Default view renders each emoji next to its name and id. Pass ``raw: True`` to get
copy-paste-ready lines for the CUSTOM map in utils/emojis.py.
"""

from __future__ import annotations

import discord

from utils.embeds import error_embed


def _chunk_messages(lines: list[str], limit: int = 1900) -> list[str]:
    """Pack lines into as few messages as possible without crossing ``limit``."""
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


async def handle(interaction: discord.Interaction, raw: bool = False) -> None:
    # Acknowledge immediately - the owner check does an HTTP fetch and would
    # otherwise blow the 3s response window (error 10062: Unknown interaction).
    await interaction.response.defer(ephemeral=True, thinking=True)

    if not await interaction.client.is_owner(interaction.user):
        await interaction.followup.send(
            embed=error_embed("Only the bot owner can view application emojis."), ephemeral=True
        )
        return

    emojis = sorted(await interaction.client.fetch_application_emojis(), key=lambda e: e.name.lower())

    if not emojis:
        await interaction.followup.send("This bot has no application emojis yet. Add some with `/emoji add`.", ephemeral=True)
        return

    if raw:
        # Lines ready to paste into the CUSTOM dict in utils/emojis.py.
        body = "\n".join(f'    "{e.name}": "<{"a" if e.animated else ""}:{e.name}:{e.id}>",' for e in emojis)
        pages = _chunk_messages(body.split("\n"), limit=1850)
        for i, page in enumerate(pages):
            header = f"**{len(emojis)} application emoji(s)** · raw ({i + 1}/{len(pages)})\n" if i == 0 else ""
            await interaction.followup.send(f"{header}```py\n{page}\n```", ephemeral=True)
        return

    lines = [f"{e} `{e.name}` · `{e.id}`" for e in emojis]
    pages = _chunk_messages(lines)
    for i, page in enumerate(pages):
        header = f"**{len(emojis)} application emoji(s)** ({i + 1}/{len(pages)})\n" if i == 0 else ""
        await interaction.followup.send(f"{header}{page}", ephemeral=True)
