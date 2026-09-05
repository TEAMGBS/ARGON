import discord
from discord import app_commands
from discord.ext import commands as ext_commands

from cogs.reminders.duration import time_autocomplete
from utils.resolver import clan_autocomplete

from .commands.edit_war_logs import handle as edit_war_logs
from .commands.list_war_logs import handle as list_war_logs
from .commands.remove_war_logs import handle as remove_war_logs
from .commands.war_logs import handle as war_logs
from .lookups import warlog_autocomplete

_MANAGE = discord.Permissions(manage_guild=True)

_WAR_TYPE_CHOICES = [
    app_commands.Choice(name="Normal", value="normal"),
    app_commands.Choice(name="CWL", value="cwl"),
    app_commands.Choice(name="Friendly", value="friendly"),
]


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
                type="Which war type to log (defaults to all)",
                time="When to post the phase embed before war ends, e.g. 18h, 12h, 6h, 1h",
                channel="Channel to post war logs in (defaults to here)",
            )(
                app_commands.autocomplete(clan=clan_autocomplete, time=time_autocomplete)(
                    app_commands.choices(type=_WAR_TYPE_CHOICES)(war_logs)
                )
            )
        )
        self.setup_group.command(name="edit-war-logs", description="Edit an existing war log")(
            app_commands.describe(
                warlog_id="The war log to edit",
                type="Change the war type",
                time="Change the phase-embed times, e.g. 18h, 12h, 6h",
                channel="Move the war log to another channel",
            )(
                app_commands.autocomplete(warlog_id=warlog_autocomplete, time=time_autocomplete)(
                    app_commands.choices(type=_WAR_TYPE_CHOICES)(edit_war_logs)
                )
            )
        )
        self.setup_group.command(name="rmwar-log", description="Remove a war log by its id")(
            app_commands.describe(warlog_id="The war log to remove")(
                app_commands.autocomplete(warlog_id=warlog_autocomplete)(remove_war_logs)
            )
        )
        self.setup_group.command(name="list-war-logs", description="List the war logs on this server")(list_war_logs)

        bot.tree.add_command(self.setup_group)

    async def cog_unload(self):
        self.bot.tree.remove_command("setup")


async def setup(bot):
    from .tasks import WarLogScheduler

    await bot.add_cog(ServerSetup(bot))
    await bot.add_cog(WarLogScheduler(bot))
