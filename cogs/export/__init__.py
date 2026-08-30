import csv
import io

import discord
from discord import app_commands
from discord.ext import commands as ext_commands

from utils.embeds import error_embed
from utils.resolver import clan_autocomplete, resolve_clan


async def members(interaction: discord.Interaction, tag: str = None):
    await interaction.response.defer()
    try:
        clan = await resolve_clan(interaction, tag)
    except ValueError as err:
        await interaction.followup.send(embed=error_embed(str(err)))
        return

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["Name", "Tag", "Role", "TownHall", "Trophies", "Donations", "Received", "League"])
    for m in clan.members:
        writer.writerow(
            [m.name, m.tag, str(m.role), m.town_hall, m.trophies, m.donations, m.received, m.league.name if m.league else ""]
        )
    buffer.seek(0)
    file = discord.File(io.BytesIO(buffer.getvalue().encode("utf-8")), filename=f"{clan.tag.strip('#')}-members.csv")
    await interaction.followup.send(content=f"{clan.name}, {clan.member_count} members exported.", file=file)


class export(ext_commands.Cog):
    """Export clan data."""

    def __init__(self, bot):
        self.bot = bot
        self.group = app_commands.Group(name="export", description="Export clan data")
        self.group.command(name="members", description="Export a clan's members as a CSV file")(
            app_commands.describe(tag="Clan tag or alias. Defaults to this server's linked clan.")(
                app_commands.autocomplete(tag=clan_autocomplete)(members)
            )
        )
        bot.tree.add_command(self.group)

    async def cog_unload(self):
        self.bot.tree.remove_command("export")


async def setup(bot):
    await bot.add_cog(export(bot))
