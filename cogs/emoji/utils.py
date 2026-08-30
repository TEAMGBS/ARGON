"""Helpers for the emoji cog: parse emoji tokens, download images, dev check.

Application emojis are global to the bot, so these commands are restricted to the
bot developer (BOT_DEV id) or the application owner.
"""

import re

import aiohttp

from config import BOT_DEV_ID

# Accepts a full custom emoji <a:name:id>, a name:id pair, or a bare id.
_FULL = re.compile(r"<(a?):([A-Za-z0-9_]{2,32}):(\d+)>")
_NAMED = re.compile(r"^([A-Za-z0-9_]{2,32}):(\d+)$")
_ID = re.compile(r"^(\d+)$")


async def is_dev(interaction) -> bool:
    """True if the caller is the configured dev, or the application owner."""
    if BOT_DEV_ID and interaction.user.id == BOT_DEV_ID:
        return True
    try:
        return await interaction.client.is_owner(interaction.user)
    except Exception:
        return False


def clean_name(name, fallback_id) -> str:
    """Discord emoji names allow only letters, digits and underscores, 2 to 32 chars."""
    name = re.sub(r"[^A-Za-z0-9_]", "", name or "")
    if len(name) < 2:
        name = f"emoji_{fallback_id}"
    return name[:32]


def parse_emoji_tokens(raw):
    """Yield (name, emoji_id) from a free-form string of ids, name:id, or <:name:id>."""
    for token in re.split(r"[\s,]+", (raw or "").strip()):
        if not token:
            continue
        full = _FULL.match(token)
        if full:
            yield clean_name(full.group(2), full.group(3)), full.group(3)
            continue
        named = _NAMED.match(token)
        if named:
            yield clean_name(named.group(1), named.group(2)), named.group(2)
            continue
        bare = _ID.match(token)
        if bare:
            yield f"emoji_{bare.group(1)}", bare.group(1)


async def download_emoji(session, emoji_id):
    """Fetch emoji image bytes from Discord's CDN, preferring the animated GIF."""
    for ext in ("gif", "png"):
        url = f"https://cdn.discordapp.com/emojis/{emoji_id}.{ext}?size=128"
        try:
            async with session.get(url) as resp:
                if resp.status == 200:
                    return await resp.read()
        except aiohttp.ClientError:
            continue
    return None
