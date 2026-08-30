"""/emoji show, list every application emoji the bot owns and attach a file of them.

The file is handy for populating utils/emojis.py: each line is ready to paste as a
Python constant, and there is a plain mention list too.
"""

import io

import discord

from utils.embeds import error_embed
from ..utils import is_dev


async def show(interaction: discord.Interaction):
    if not await is_dev(interaction):
        await interaction.response.send_message(
            embed=error_embed("This command is restricted to the bot developer."), ephemeral=True
        )
        return

    await interaction.response.defer()
    emojis = await interaction.client.fetch_application_emojis()
    if not emojis:
        await interaction.followup.send(
            embed=error_embed("The bot has no application emojis yet. Add some with `/emoji bulkadd`.")
        )
        return

    ordered = sorted(emojis, key=lambda e: e.name.lower())

    # Build a text file: a Python-constant block, then a plain mention list.
    const_lines = [f'{e.name.upper()} = "{str(e)}"' for e in ordered]
    mention_lines = [f"{e.name}: {str(e)}  (id {e.id})" for e in ordered]
    contents = (
        "# Paste these into utils/emojis.py\n"
        + "\n".join(const_lines)
        + "\n\n# Reference list\n"
        + "\n".join(mention_lines)
        + "\n"
    )
    file = discord.File(io.BytesIO(contents.encode("utf-8")), filename="argon_emojis.txt")

    # Also show a preview inline, in chunks that fit Discord's field limits.
    preview = " ".join(str(e) for e in ordered)
    embed = discord.Embed(
        title=f"Application emojis ({len(ordered)})",
        description=preview[:4000],
        color=discord.Color.blurple(),
    )
    embed.set_footer(text="Full list attached as argon_emojis.txt")
    await interaction.followup.send(embed=embed, file=file)
