import discord
from discord import app_commands
from discord.ext import commands as ext_commands

from .commands.army import army
from .commands.info import info
from .commands.rushed import rushed
from .commands.units import units
from .commands.upgrades import upgrades

# Options shared by the player lookup commands.
_describe = app_commands.describe(
    tag="A CoC player tag (e.g. #ABC123). Defaults to your linked account.",
    user="Look up another Discord user's linked account.",
)


class player(ext_commands.Cog):
    """Player profile and progress commands."""

    def __init__(self, bot):
        self.bot = bot
        self.group = app_commands.Group(name="player", description="Player profile and stats")

        self.group.command(name="info", description="Show a player's profile and stats")(_describe(info))
        self.group.command(name="units", description="Show a player's troop, spell and hero levels")(_describe(units))
        self.group.command(name="army", description="Show maxed hero/troop/spell progress")(_describe(army))
        self.group.command(name="rushed", description="Estimate a player's rushed units")(_describe(rushed))
        self.group.command(name="upgrades", description="List a player's available upgrades")(_describe(upgrades))

        bot.tree.add_command(self.group)

    async def cog_unload(self):
        self.bot.tree.remove_command("player")


async def setup(bot):
    await bot.add_cog(player(bot))
