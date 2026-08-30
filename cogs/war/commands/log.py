"""/war log — recent war results."""

import coc
import discord

from utils.embeds import base_embed, error_embed
from utils.emojis import E_CORRECT, E_STAR, E_WRONG
from utils.resolver import resolve_clan


async def log(interaction: discord.Interaction, tag: str = None):
    await interaction.response.defer()
    try:
        clan = await resolve_clan(interaction, tag)
    except ValueError as err:
        await interaction.followup.send(embed=error_embed(str(err)))
        return

    try:
        entries = await interaction.client.coc_client.get_war_log(clan.tag, limit=15)
    except coc.PrivateWarLog:
        await interaction.followup.send(embed=error_embed("This clan's war log is private."))
        return
    except Exception:
        await interaction.followup.send(embed=error_embed("Clash of Clans API request failed, try again in a bit."))
        return

    if not entries:
        await interaction.followup.send(embed=error_embed("This clan has no war log entries."))
        return

    def icon(result):
        return E_CORRECT if result == "win" else E_WRONG if result == "lose" else "➖"

    lines = []
    for w in entries:
        opp = w.opponent.name if w.opponent and w.opponent.name else "Unknown (CWL)"
        opp_stars = w.opponent.stars if w.opponent else 0
        lines.append(f"{icon(w.result)} vs **{opp}** — {E_STAR} {w.clan.stars}-{opp_stars} • {w.clan.destruction:.1f}%")

    embed = await base_embed(interaction, title=f"{clan.name} ({clan.tag}) — War Log")
    embed.description = "\n".join(lines)[:4000]
    await interaction.followup.send(embed=embed)
