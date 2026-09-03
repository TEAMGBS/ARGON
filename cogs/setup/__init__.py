import discord
from discord import app_commands
from discord.ext import commands as ext_commands

from .commands.log import log

# Log-type choices for /setup log.
_LOG_CHOICES = [
    app_commands.Choice(name="Member join/leave log", value="member"),
    app_commands.Choice(name="Donation log", value="donation"),
    app_commands.Choice(name="Clan feed", value="feed"),
]

_MANAGE = discord.Permissions(manage_guild=True)


class ServerSetup(ext_commands.Cog):
    """Configure logs for the clans added to this server (via /alliance add-clan)."""

    def __init__(self, bot):
        self.bot = bot

        self.setup_group = app_commands.Group(
            name="setup", description="Configure clan logs", default_permissions=_MANAGE, guild_only=True
        )
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
