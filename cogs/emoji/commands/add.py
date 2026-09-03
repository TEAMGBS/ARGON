"""/emoji add, mass-upload application emojis to the bot from ids or mentions.

Application emojis belong to the bot itself (not a server), so once uploaded they
work in every guild the bot is in. This command accepts, in one blob, any mix of:

  * custom emoji mentions      <:name:123456789012345678>  /  <a:name:...>
  * "name id" / "name:id" pairs   cwllegend 123456789012345678
  * bare ids                    123456789012345678   (named e<id>)

Each is downloaded from Discord's CDN and re-uploaded as an application emoji.
"""

from __future__ import annotations

import re

import aiohttp
import discord

from utils.embeds import error_embed

# <a:name:id> or <:name:id>
_MENTION_RE = re.compile(r"<(a?):([A-Za-z0-9_]{2,32}):(\d{15,25})>")
# "name id", "name:id", or a bare id, one per whitespace/comma/newline chunk.
_PAIR_RE = re.compile(r"(?:([A-Za-z0-9_]{2,32})\s*[:=]?\s*)?(\d{15,25})")


def _sanitize_name(name: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_]", "_", name or "").strip("_")
    if len(cleaned) < 2:
        cleaned = f"e_{cleaned}" if cleaned else "emoji"
    return cleaned[:32]


def parse_emojis(text: str) -> list[tuple[str, int, bool]]:
    """Return a de-duplicated list of (name, id, animated) parsed from ``text``."""
    found: dict[int, tuple[str, int, bool]] = {}

    for animated, name, eid in _MENTION_RE.findall(text):
        eid = int(eid)
        found[eid] = (_sanitize_name(name), eid, animated == "a")

    # Strip mentions we already parsed, then look for loose name/id pairs.
    remainder = _MENTION_RE.sub(" ", text)
    for name, eid in _PAIR_RE.findall(remainder):
        eid = int(eid)
        if eid in found:
            continue
        found[eid] = (_sanitize_name(name) if name else f"e{eid}", eid, False)

    return list(found.values())


async def _download(session: aiohttp.ClientSession, eid: int, animated: bool) -> bytes | None:
    """Fetch an emoji image from the CDN, trying the other extension as a fallback."""
    exts = ["gif", "png"] if animated else ["png", "gif"]
    for ext in exts:
        url = f"https://cdn.discordapp.com/emojis/{eid}.{ext}"
        try:
            async with session.get(url) as resp:
                if resp.status == 200:
                    return await resp.read()
        except Exception:
            continue
    return None


async def handle(interaction: discord.Interaction, emojis: str) -> None:
    if not await interaction.client.is_owner(interaction.user):
        await interaction.response.send_message(
            embed=error_embed("Only the bot owner can manage application emojis."), ephemeral=True
        )
        return

    parsed = parse_emojis(emojis)
    if not parsed:
        await interaction.response.send_message(
            embed=error_embed("No emoji ids or mentions found. Paste `<:name:id>` mentions or `name id` pairs."),
            ephemeral=True,
        )
        return

    await interaction.response.defer(ephemeral=True, thinking=True)

    existing = {e.name.lower() for e in await interaction.client.fetch_application_emojis()}

    added, skipped, failed = [], [], []
    async with aiohttp.ClientSession() as session:
        for name, eid, animated in parsed:
            if name.lower() in existing:
                skipped.append(name)
                continue
            data = await _download(session, eid, animated)
            if data is None:
                failed.append(f"{name} (`{eid}`) — image not found")
                continue
            try:
                created = await interaction.client.create_application_emoji(name=name, image=data)
                existing.add(created.name.lower())
                added.append(f"{created} {created.name}")
            except discord.HTTPException as exc:
                failed.append(f"{name} (`{eid}`) — {exc.text or exc}")

    lines = [f"**Added {len(added)}** · **Skipped {len(skipped)}** · **Failed {len(failed)}**"]
    if added:
        lines.append("\n**Added:** " + "  ".join(added)[:1500])
    if skipped:
        lines.append("\n**Already existed:** " + ", ".join(skipped)[:800])
    if failed:
        lines.append("\n**Failed:**\n" + "\n".join(failed)[:1500])

    await interaction.followup.send("\n".join(lines)[:2000], ephemeral=True)
