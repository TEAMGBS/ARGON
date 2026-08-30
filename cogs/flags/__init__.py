import discord
from discord import app_commands
from discord.ext import commands as ext_commands

from .commands.add import flag_add
from .commands.list_ import flag_list
from .commands.remove import flag_remove

_MANAGE = discord.Permissions(manage_guild=True)


class flags(ext_commands.Cog):
    """Flag players for monitoring."""

    def __init__(self, bot):
        self.bot = bot
        self.group = app_commands.Group(
            name="flag", description="Flag players for monitoring", default_permissions=_MANAGE, guild_only=True
        )
        self.group.command(name="add", description="Flag a player")(
            app_commands.describe(tag="Player tag", reason="Reason for the flag")(flag_add)
        )
        self.group.command(name="remove", description="Remove a flag")(
            app_commands.describe(tag="Player tag")(flag_remove)
        )
        self.group.command(name="list", description="List flagged players")(flag_list)

        bot.tree.add_command(self.group)

    async def cog_unload(self):
        self.bot.tree.remove_command("flag")


async def setup(bot):
    await bot.add_cog(flags(bot))
