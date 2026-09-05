"""/war info, show a clan's current-war board on demand (same as the war logs)."""

from __future__ import annotations

import coc
import discord

from cogs.setup.warembed import build_war_view, phase_meta, war_type
from database.db import get_pool
from utils.embeds import error_embed
from utils.tags import is_valid_tag, normalize_tag


async def handle(interaction: discord.Interaction, clan: str | None = None, type: str | None = None) -> None:
    await interaction.response.defer()

    if clan:
        if not is_valid_tag(clan):
            await interaction.followup.send(embed=error_embed(f"`{clan}` is not a valid clan tag."))
            return
        tag = normalize_tag(clan)
    else:
        pool = await get_pool()
        row = await pool.fetchrow(
            "SELECT tag FROM clan_stores WHERE guild_id = $1 ORDER BY created_at LIMIT 1", interaction.guild_id
        )
        if not row:
            await interaction.followup.send(
                embed=error_embed("No clan given and no alliance clans added. Use `/alliance add-clan`.")
            )
            return
        tag = row["tag"]

    try:
        war = await interaction.client.coc_client.get_current_war(tag)
    except coc.PrivateWarLog:
        await interaction.followup.send(embed=error_embed(f"`{tag}`'s war log is private, so the war can't be read."))
        return
    except coc.NotFound:
        await interaction.followup.send(embed=error_embed(f"No clan found for `{tag}`."))
        return
    except Exception:
        await interaction.followup.send(embed=error_embed("Couldn't fetch the war right now, try again in a bit."))
        return

    if war is None or war.state == "notInWar":
        await interaction.followup.send(embed=error_embed(f"`{tag}` is not in a war right now."))
        return

    if type and war_type(war) != type:
        await interaction.followup.send(
            embed=error_embed(f"`{tag}` has no active **{type}** war right now (current war is **{war_type(war)}**).")
        )
        return

    label, color, ended = phase_meta(war)
    await interaction.followup.send(view=build_war_view(war, label, color, ended))
