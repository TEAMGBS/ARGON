import discord
from discord import app_commands
from discord.ext import commands as ext_commands

from .commands.add_clan import handle as add_clan
from .commands.info_clans import handle as info_clans
from .commands.remove_clan import handle as remove_clan
from .commands.show_clans import handle as show_clans

_MANAGE = discord.Permissions(manage_guild=True)


class alliance(ext_commands.Cog):
    """Manage the clans that belong to this server. Add a clan before setting up logs or reminders."""

    def __init__(self, bot):
        self.bot = bot
        self.group = app_commands.Group(
            name="alliance", description="Manage the clans in this server", default_permissions=_MANAGE, guild_only=True
        )

        self.group.command(name="add-clan", description="Add a clan to this server")(
            app_commands.describe(tag="Clan tag, e.g. #2PP0")(add_clan)
        )
        self.group.command(name="remove-clan", description="Remove a clan and its logs and reminders")(
            app_commands.describe(tag="Clan tag")(remove_clan)
        )
        self.group.command(name="show-clans", description="List the clans added to this server")(show_clans)
        self.group.command(name="info-clans", description="Show live details for each added clan")(info_clans)

        bot.tree.add_command(self.group)

    async def cog_unload(self):
        self.bot.tree.remove_command("alliance")


async def setup(bot):
    await bot.add_cog(alliance(bot))
