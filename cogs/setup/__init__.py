import discord
from discord import app_commands
from discord.ext import commands as ext_commands

from utils.resolver import clan_autocomplete

from .commands.war_logs import handle as war_logs

_MANAGE = discord.Permissions(manage_guild=True)


class ServerSetup(ext_commands.Cog):
    """Configure war logs for the clans added to this server (via /alliance add-clan)."""

    def __init__(self, bot):
        self.bot = bot

        self.setup_group = app_commands.Group(
            name="setup", description="Configure clan war logs", default_permissions=_MANAGE, guild_only=True
        )
        self.setup_group.command(name="war-logs", description="Post a clan's war hits and war-phase updates to a channel")(
            app_commands.describe(
                clan="An alliance clan (added with /alliance add-clan)",
                channel="Channel to post war logs in (defaults to here)",
            )(app_commands.autocomplete(clan=clan_autocomplete)(war_logs))
        )

        bot.tree.add_command(self.setup_group)

    async def cog_unload(self):
        self.bot.tree.remove_command("setup")


async def setup(bot):
    from .tasks import WarLogScheduler

    await bot.add_cog(ServerSetup(bot))
    await bot.add_cog(WarLogScheduler(bot))
