"""/emoji bulkadd, add emojis to the bot in bulk from ids, name:id pairs, or emojis."""

import aiohttp
import discord

from utils.embeds import error_embed
from ..utils import download_emoji, is_dev, parse_emoji_tokens


async def bulkadd(interaction: discord.Interaction, emojis: str):
    if not await is_dev(interaction):
        await interaction.response.send_message(
            embed=error_embed("This command is restricted to the bot developer."), ephemeral=True
        )
        return

    tokens = list(parse_emoji_tokens(emojis))
    if not tokens:
        await interaction.response.send_message(
            embed=error_embed("Give me emoji ids, `name:id` pairs, or the emojis themselves.")
        )
        return

    await interaction.response.defer()
    added, failed = [], []
    existing = {e.name for e in await interaction.client.fetch_application_emojis()}

    async with aiohttp.ClientSession() as session:
        for name, emoji_id in tokens:
            # Keep names unique so one clash does not abort the whole batch.
            unique = name
            suffix = 1
            while unique in existing:
                unique = f"{name[:29]}_{suffix}"
                suffix += 1

            image = await download_emoji(session, emoji_id)
            if image is None:
                failed.append(f"`{emoji_id}` (could not fetch image)")
                continue
            try:
                created = await interaction.client.create_application_emoji(name=unique, image=image)
                existing.add(created.name)
                added.append(str(created))
            except discord.HTTPException as exc:
                failed.append(f"`{emoji_id}` ({exc.text or exc.status})")

    lines = []
    if added:
        lines.append(f"**Added {len(added)}:** " + " ".join(added))
    if failed:
        lines.append(f"**Failed {len(failed)}:** " + ", ".join(failed))
    embed = discord.Embed(
        title="Bulk emoji add",
        description="\n\n".join(lines)[:4000] or "Nothing to add.",
        color=discord.Color.green() if added else discord.Color.red(),
    )
    await interaction.followup.send(embed=embed)
