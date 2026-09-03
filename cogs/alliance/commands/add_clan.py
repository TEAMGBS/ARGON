"""/alliance add-clan, add a clan to this server so logs and reminders can be set up for it."""

from __future__ import annotations

import discord
from discord import app_commands

from database import clans as clans_db
from utils.embeds import error_embed, format_tag, success_embed
from utils.tags import is_valid_tag

# The categories every server starts with. A server can invent new ones simply by
# typing them into the `category` option - the autocomplete then remembers them.
DEFAULT_CATEGORIES = ("competitive", "casual", "fwa")


def normalize_category(raw: str | None) -> str:
    """Lower-case, trim, and collapse whitespace; empty falls back to 'casual'."""
    cleaned = " ".join((raw or "").split()).lower()
    return cleaned or "casual"


async def handle(interaction: discord.Interaction, tag: str, category: str = "casual") -> None:
    if not is_valid_tag(tag):
        await interaction.response.send_message(embed=error_embed("That is not a valid clan tag."), ephemeral=True)
        return

    await interaction.response.defer()
    tag = format_tag(tag)
    category = normalize_category(category)

    try:
        clan = await interaction.client.coc_client.get_clan(tag)
    except Exception:
        await interaction.followup.send(embed=error_embed(f"No clan found for `{tag}`."))
        return

    await clans_db.add_clan(interaction.guild_id, tag, clan.name, category)
    await interaction.followup.send(
        embed=success_embed(
            f"Added **{clan.name}** (`{tag}`) to the **{category}** category. "
            "You can now set up logs and reminders for it."
        )
    )


async def category_autocomplete(interaction: discord.Interaction, current: str) -> list[app_commands.Choice]:
    """Suggest the default categories plus any this server has already created.

    The user can still type a brand-new category - autocomplete never forces a
    choice, it only offers the ones we know about.
    """
    known = list(DEFAULT_CATEGORIES)
    if interaction.guild_id:
        try:
            for existing in await clans_db.get_categories_for_guild(interaction.guild_id):
                if existing not in known:
                    known.append(existing)
        except Exception:
            pass

    query = normalize_category(current) if current else ""
    # If the user is typing something new, offer it as the first choice too.
    if query and query not in known:
        known.insert(0, query)

    choices = [c for c in known if not query or query in c]
    return [app_commands.Choice(name=c.title(), value=c) for c in choices[:25]]
