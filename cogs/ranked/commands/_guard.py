"""Shared permission guard for the admin-only ranked commands.

The ranked group can't use default_member_permissions (that would also lock
card-player, which is public), so the admin commands check Manage Server here.
"""

from __future__ import annotations

import discord

from utils.embeds import error_embed


async def require_manage(interaction: discord.Interaction) -> bool:
    perms = interaction.user.guild_permissions if interaction.guild else None
    if perms and perms.manage_guild:
        return True
    await interaction.response.send_message(
        embed=error_embed("You need the **Manage Server** permission to use this."), ephemeral=True
    )
    return False
