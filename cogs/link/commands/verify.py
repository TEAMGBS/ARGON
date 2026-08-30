"""/link verify, prove account ownership with the in-game API token."""

import discord

from database.db import get_pool
from utils.embeds import error_embed, success_embed
from utils.tags import is_valid_tag, normalize_tag


async def verify(interaction: discord.Interaction, tag: str, token: str):
    await interaction.response.defer(ephemeral=True)

    if not is_valid_tag(tag):
        await interaction.followup.send(embed=error_embed("That is not a valid player tag."))
        return
    tag = normalize_tag(tag)

    try:
        ok = await interaction.client.coc_client.verify_player_token(tag, token.strip())
    except Exception:
        ok = False
    if not ok:
        await interaction.followup.send(
            embed=error_embed("Verification failed. Double-check the tag and the in-game API token.")
        )
        return

    try:
        player = await interaction.client.coc_client.get_player(tag)
        name = player.name
    except Exception:
        name = tag

    pool = await get_pool()
    # Upsert: verify an existing link, or create a verified one.
    await pool.execute(
        """INSERT INTO linked_accounts (discord_id, tag, name, verified)
           VALUES ($1, $2, $3, TRUE)
           ON CONFLICT (tag) DO UPDATE SET verified = TRUE, name = EXCLUDED.name, discord_id = $1""",
        interaction.user.id,
        tag,
        name,
    )
    await interaction.followup.send(embed=success_embed(f"Verified ownership of **{name}** (`{tag}`)."))
