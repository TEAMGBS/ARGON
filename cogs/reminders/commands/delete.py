"""/reminders delete, remove a reminder by its id."""

from __future__ import annotations

import discord

from database import reminders as reminders_db
from utils.embeds import error_embed, success_embed


async def handle(interaction: discord.Interaction, reminder_id: str) -> None:
    reminder_id = reminder_id.strip().upper()
    row = await reminders_db.get_reminder(reminder_id)
    if not row or row["guild_id"] != interaction.guild_id:
        await interaction.response.send_message(
            embed=error_embed(f"No reminder found with ID `{reminder_id}`."), ephemeral=True
        )
        return
    await reminders_db.delete_reminder(reminder_id)
    await interaction.response.send_message(embed=success_embed(f"Reminder `{reminder_id}` deleted."))
