import discord
from discord import app_commands
from discord.ext import commands as ext_commands

from .commands.clan import clan_add, clan_list, clan_remove
from .commands.log import log

# Log-type choices for /setup log.
_LOG_CHOICES = [
    app_commands.Choice(name="Member join/leave log", value="member"),
    app_commands.Choice(name="Donation log", value="donation"),
    app_commands.Choice(name="Clan feed", value="feed"),
]

_MANAGE = discord.Permissions(manage_guild=True)


class ServerSetup(ext_commands.Cog):
    """Link clans to this server and configure their logs."""

    def __init__(self, bot):
        self.bot = bot

        self.setup_group = app_commands.Group(
            name="setup", description="Link clans and configure logs", default_permissions=_MANAGE, guild_only=True
        )
        self.setup_group.command(name="clan", description="Link a clan to this server")(
            app_commands.describe(tag="Clan tag")(clan_add)
        )
        self.setup_group.command(name="remove", description="Unlink a clan from this server")(
            app_commands.describe(tag="Clan tag")(clan_remove)
        )
        self.setup_group.command(name="list", description="List clans linked to this server")(clan_list)
        self.setup_group.command(name="log", description="Enable a log/feed for a clan in a channel")(
            app_commands.describe(tag="Clan tag", log_type="Which log to enable", channel="Target channel")(
                app_commands.choices(log_type=_LOG_CHOICES)(log)
            )
        )

        bot.tree.add_command(self.setup_group)

    async def cog_unload(self):
        self.bot.tree.remove_command("setup")


async def setup(bot):
    await bot.add_cog(ServerSetup(bot))
