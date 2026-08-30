import discord
from discord import app_commands
from discord.ext import commands as ext_commands

from .commands.bulkadd import bulkadd
from .commands.show import show


class emoji(ext_commands.Cog):
    """Manage the bot's application emojis (developer only)."""

    def __init__(self, bot):
        self.bot = bot
        self.group = app_commands.Group(name="emoji", description="Manage the bot's application emojis")

        self.group.command(name="show", description="List all of the bot's emojis and attach them as a file")(show)
        self.group.command(name="bulkadd", description="Add emojis to the bot in bulk by id")(
            app_commands.describe(
                emojis="Emoji ids, name:id pairs, or the emojis themselves, separated by spaces or commas"
            )(bulkadd)
        )

        bot.tree.add_command(self.group)

    async def cog_unload(self):
        self.bot.tree.remove_command("emoji")


async def setup(bot):
    await bot.add_cog(emoji(bot))
