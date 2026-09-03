import discord
from discord import app_commands
from discord.ext import commands as ext_commands

from .commands.add import handle as add_emoji
from .commands.show import handle as show_emoji

_MANAGE = discord.Permissions(manage_guild=True)


class emoji(ext_commands.Cog):
    """Owner-only management of the bot's application emojis (mass add + list)."""

    def __init__(self, bot):
        self.bot = bot
        self.group = app_commands.Group(
            name="emoji", description="Manage the bot's application emojis", default_permissions=_MANAGE
        )

        self.group.command(name="add", description="Bulk add application emojis from ids or mentions (owner only)")(
            app_commands.describe(
                emojis="Paste emoji mentions like <:name:id> and/or 'name id' pairs, separated by spaces or new lines"
            )(add_emoji)
        )
        self.group.command(name="show", description="List the bot's application emojis (owner only)")(
            app_commands.describe(raw="Output copy paste lines for utils/emojis.py instead of a rendered list")(
                show_emoji
            )
        )

        bot.tree.add_command(self.group)

    async def cog_unload(self):
        self.bot.tree.remove_command("emoji")


async def setup(bot):
    await bot.add_cog(emoji(bot))
