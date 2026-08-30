"""/config — per-server settings (embed color, timezone)."""

import discord

from database.db import get_pool
from utils.embeds import base_embed, error_embed


async def config(interaction: discord.Interaction, color: str = None, timezone: str = None):
    await interaction.response.defer()
    pool = await get_pool()

    if color is not None:
        hex_value = color.lstrip("#")
        if len(hex_value) != 6 or any(c not in "0123456789abcdefABCDEF" for c in hex_value):
            await interaction.followup.send(embed=error_embed("Color must be a 6-digit hex, e.g. `5865F2`."))
            return
        await pool.execute(
            """INSERT INTO guild_settings (guild_id, color) VALUES ($1, $2)
               ON CONFLICT (guild_id) DO UPDATE SET color = EXCLUDED.color, updated_at = NOW()""",
            interaction.guild_id,
            hex_value,
        )
    if timezone is not None:
        await pool.execute(
            """INSERT INTO guild_settings (guild_id, timezone) VALUES ($1, $2)
               ON CONFLICT (guild_id) DO UPDATE SET timezone = EXCLUDED.timezone, updated_at = NOW()""",
            interaction.guild_id,
            timezone,
        )

    row = await pool.fetchrow("SELECT color, timezone FROM guild_settings WHERE guild_id = $1", interaction.guild_id)
    embed = await base_embed(interaction, title="Server Settings")
    embed.description = "✅ Updated." if (color or timezone) else "Current configuration:"
    embed.add_field(name="Embed color", value=f"#{(row['color'] if row and row['color'] else '5865F2')}", inline=True)
    embed.add_field(name="Timezone", value=(row["timezone"] if row and row["timezone"] else "UTC"), inline=True)
    await interaction.followup.send(embed=embed)
