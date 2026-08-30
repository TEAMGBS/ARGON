import discord
from discord import app_commands
from discord.ext import commands as ext_commands

from .commands.add import reminder_add
from .commands.list_ import reminder_list
from .commands.remove import reminder_remove

_MANAGE = discord.Permissions(manage_guild=True)


class reminders(ext_commands.Cog):
    """Manage war reminders."""

    def __init__(self, bot):
        self.bot = bot
        self.group = app_commands.Group(
            name="reminders", description="Manage war reminders", default_permissions=_MANAGE, guild_only=True
        )
        self.group.command(name="add", description="Create a war reminder")(
            app_commands.describe(
                before="Minutes before war end to fire (5-1440)",
                tag="Clan tag",
                channel="Channel to post in",
                message="Custom message",
                min_remaining="Only ping members with at least this many attacks left (1-2)",
                role="Role to mention",
            )(reminder_add)
        )
        self.group.command(name="list", description="List war reminders")(reminder_list)
        self.group.command(name="remove", description="Delete a reminder by its number")(
            app_commands.describe(index="Reminder number (from /reminders list)")(reminder_remove)
        )
        bot.tree.add_command(self.group)

    async def cog_unload(self):
        self.bot.tree.remove_command("reminders")


async def setup(bot):
    from .tasks import Scheduler

    await bot.add_cog(reminders(bot))
    await bot.add_cog(Scheduler(bot))
