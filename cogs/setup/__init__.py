import discord
from discord import app_commands
from discord.ext import commands as ext_commands

from .commands.alias import alias_add, alias_list, alias_remove
from .commands.clan import clan_add, clan_list, clan_remove
from .commands.config import config as config_impl
from .commands.log import log

# Log-type choices for /setup log.
_LOG_CHOICES = [
    app_commands.Choice(name="Member join/leave log", value="member"),
    app_commands.Choice(name="Donation log", value="donation"),
    app_commands.Choice(name="Clan feed", value="feed"),
]

_MANAGE = discord.Permissions(manage_guild=True)


class ServerSetup(ext_commands.Cog):
    """Server configuration: link clans, logs, aliases and settings."""

    def __init__(self, bot):
        self.bot = bot

        # /setup ...
        self.setup_group = app_commands.Group(
            name="setup", description="Link clans and configure logs", default_permissions=_MANAGE, guild_only=True
        )
        self.setup_group.command(name="clan", description="Link a clan to this server")(
            app_commands.describe(tag="Clan tag", alias="Optional short alias for this clan")(clan_add)
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

        # /alias ...
        self.alias_group = app_commands.Group(
            name="alias", description="Manage clan tag aliases", default_permissions=_MANAGE, guild_only=True
        )
        self.alias_group.command(name="add", description="Create an alias for a clan tag")(
            app_commands.describe(name="Alias name", tag="Clan tag")(alias_add)
        )
        self.alias_group.command(name="remove", description="Delete an alias")(
            app_commands.describe(name="Alias name")(alias_remove)
        )
        self.alias_group.command(name="list", description="List all aliases")(alias_list)

        bot.tree.add_command(self.setup_group)
        bot.tree.add_command(self.alias_group)

    # /config, registered automatically when the cog is added.
    @app_commands.command(name="config", description="View or change server settings")
    @app_commands.describe(color="Embed color hex, e.g. 5865F2", timezone="Server timezone id, e.g. Europe/London")
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.guild_only()
    async def config(self, interaction: discord.Interaction, color: str = None, timezone: str = None):
        await config_impl(interaction, color=color, timezone=timezone)

    async def cog_unload(self):
        self.bot.tree.remove_command("setup")
        self.bot.tree.remove_command("alias")


async def setup(bot):
    await bot.add_cog(ServerSetup(bot))
