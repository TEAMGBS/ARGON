"""/setup clan|remove|list, link clans to this server."""

import discord

from database.db import get_pool
from utils.embeds import base_embed, error_embed, success_embed
from utils.emojis import E_CLAN
from utils.tags import is_valid_tag, normalize_tag


async def clan_add(interaction: discord.Interaction, tag: str):
    await interaction.response.defer()
    if not is_valid_tag(tag):
        await interaction.followup.send(embed=error_embed("Invalid clan tag."))
        return
    tag = normalize_tag(tag)

    try:
        clan = await interaction.client.coc_client.get_clan(tag)
    except Exception:
        await interaction.followup.send(embed=error_embed(f"No clan found for `{tag}`."))
        return

    pool = await get_pool()
    await pool.execute(
        """INSERT INTO clan_stores (guild_id, tag, name) VALUES ($1, $2, $3)
           ON CONFLICT (guild_id, tag) DO UPDATE SET name = EXCLUDED.name""",
        interaction.guild_id,
        tag,
        clan.name,
    )
    await interaction.followup.send(embed=success_embed(f"Linked **{clan.name}** (`{tag}`) to this server."))


async def clan_remove(interaction: discord.Interaction, tag: str):
    await interaction.response.defer()
    tag = normalize_tag(tag)
    pool = await get_pool()
    result = await pool.execute("DELETE FROM clan_stores WHERE guild_id = $1 AND tag = $2", interaction.guild_id, tag)
    await pool.execute("DELETE FROM clan_snapshots WHERE guild_id = $1 AND tag = $2", interaction.guild_id, tag)
    await pool.execute("DELETE FROM clan_logs WHERE guild_id = $1 AND tag = $2", interaction.guild_id, tag)
    if result.endswith("0"):
        await interaction.followup.send(embed=error_embed(f"`{tag}` is not linked here."))
        return
    await interaction.followup.send(embed=success_embed(f"Unlinked `{tag}`."))


async def clan_list(interaction: discord.Interaction):
    await interaction.response.defer()
    pool = await get_pool()
    clans = await pool.fetch("SELECT tag, name FROM clan_stores WHERE guild_id = $1 ORDER BY created_at", interaction.guild_id)
    if not clans:
        await interaction.followup.send(embed=error_embed("No clans linked. Add one with `/setup clan`."))
        return

    logs = await pool.fetch("SELECT tag, log_type, channel_id FROM clan_logs WHERE guild_id = $1", interaction.guild_id)
    logs_by_tag: dict[str, list[str]] = {}
    for row in logs:
        logs_by_tag.setdefault(row["tag"], []).append(f"{row['log_type']} → <#{row['channel_id']}>")

    lines = []
    for c in clans:
        detail = ", ".join(logs_by_tag.get(c["tag"], [])) or "no logs"
        lines.append(f"{E_CLAN} **{c['name']}** ({c['tag']})\n  {detail}")

    embed = await base_embed(interaction, title="Linked Clans")
    embed.description = "\n".join(lines)[:4000]
    await interaction.followup.send(embed=embed)
