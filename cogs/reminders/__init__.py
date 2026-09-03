import discord
from discord import app_commands
from discord.ext import commands as ext_commands

from utils.resolver import clan_autocomplete

from .commands.create import handle as create_reminder
from .commands.delete import handle as delete_reminder
from .commands.list import handle as list_reminders

_MANAGE = discord.Permissions(manage_guild=True)

_TYPE_CHOICES = [
    app_commands.Choice(name="Clan War", value="war"),
    app_commands.Choice(name="Capital Raid", value="capital"),
    app_commands.Choice(name="Clan Games", value="cg"),
]


async def _create_command(
    interaction: discord.Interaction,
    type: str,
    clan_tag: str,
    message: str | None = None,
    channel: discord.TextChannel | None = None,
):
    # `type` is a str because the parameter is annotated str (discord.py passes the choice value).
    await create_reminder(interaction, type, clan_tag, message, channel)


class reminders(ext_commands.Cog):
    """Create and manage reminders for the server's clans."""

    def __init__(self, bot):
        self.bot = bot
        self.group = app_commands.Group(
            name="reminders", description="Manage clan reminders", default_permissions=_MANAGE, guild_only=True
        )

        self.group.command(name="create", description="Create a reminder for a clan")(
            app_commands.describe(
                type="What the reminder is for",
                clan_tag="A clan added to this server",
                message="Optional message to include",
                channel="Channel to post in (defaults to here)",
            )(
                app_commands.autocomplete(clan_tag=clan_autocomplete)(
                    app_commands.choices(type=_TYPE_CHOICES)(_create_command)
                )
            )
        )
        self.group.command(name="list", description="List active reminders")(list_reminders)
        self.group.command(name="delete", description="Delete a reminder by its id")(
            app_commands.describe(reminder_id="The reminder id (from /reminders list)")(delete_reminder)
        )

        bot.tree.add_command(self.group)

    async def cog_unload(self):
        self.bot.tree.remove_command("reminders")


async def setup(bot):
    from .tasks import Scheduler

    await bot.add_cog(reminders(bot))
    await bot.add_cog(Scheduler(bot))
