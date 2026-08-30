"""/alias add|remove|list — short names that stand in for clan tags."""

import discord

from database.db import get_pool
from utils.embeds import base_embed, error_embed, success_embed
from utils.tags import is_valid_tag, normalize_tag


async def alias_add(interaction: discord.Interaction, name: str, tag: str):
    await interaction.response.defer()
    if not is_valid_tag(tag):
        await interaction.followup.send(embed=error_embed("Invalid clan tag."))
        return
    name = name.lower()
    pool = await get_pool()
    await pool.execute(
        """INSERT INTO aliases (guild_id, name, tag) VALUES ($1, $2, $3)
           ON CONFLICT (guild_id, name) DO UPDATE SET tag = EXCLUDED.tag""",
        interaction.guild_id,
        name,
        normalize_tag(tag),
    )
    await interaction.followup.send(embed=success_embed(f"Alias `{name}` → `{normalize_tag(tag)}`."))


async def alias_remove(interaction: discord.Interaction, name: str):
    await interaction.response.defer()
    pool = await get_pool()
    result = await pool.execute("DELETE FROM aliases WHERE guild_id = $1 AND name = $2", interaction.guild_id, name.lower())
    if result.endswith("0"):
        await interaction.followup.send(embed=error_embed(f"No alias named `{name}`."))
        return
    await interaction.followup.send(embed=success_embed(f"Deleted alias `{name}`."))


async def alias_list(interaction: discord.Interaction):
    await interaction.response.defer()
    pool = await get_pool()
    rows = await pool.fetch("SELECT name, tag FROM aliases WHERE guild_id = $1 ORDER BY name", interaction.guild_id)
    if not rows:
        await interaction.followup.send(embed=error_embed("No aliases yet. Create one with `/alias add`."))
        return
    embed = await base_embed(interaction, title="Clan Aliases")
    embed.description = "\n".join(f"`{r['name']}` → `{r['tag']}`" for r in rows)
    await interaction.followup.send(embed=embed)
