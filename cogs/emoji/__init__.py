import discord
from discord import app_commands
from discord.ext import commands as ext_commands

from .categories import category_autocomplete
from .commands.add import handle as add_emoji
from .commands.categorize import handle as categorize_emoji
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
                emojis="Paste emoji mentions like <:name:id> and/or 'name id' pairs, separated by spaces or new lines",
                category="Category to file these emojis under (autocompletes; re-add to recategorize)",
            )(app_commands.autocomplete(category=category_autocomplete)(add_emoji))
        )
        self.group.command(name="show", description="List the bot's application emojis by category (owner only)")(
            app_commands.describe(
                raw="Output copy paste lines for utils/emojis.py instead of a rendered list",
                category="Show only this category",
            )(app_commands.autocomplete(category=category_autocomplete)(show_emoji))
        )
        self.group.command(name="categorize", description="File existing emojis into a category by a name match (owner only)")(
            app_commands.describe(
                category="Category to file the matching emojis under",
                match="Only emojis whose name contains this (e.g. cwl, TH); blank = all",
            )(app_commands.autocomplete(category=category_autocomplete)(categorize_emoji))
        )

        bot.tree.add_command(self.group)

    async def cog_unload(self):
        self.bot.tree.remove_command("emoji")


async def setup(bot):
    await bot.add_cog(emoji(bot))
