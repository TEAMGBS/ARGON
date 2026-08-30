import discord
from discord import app_commands
from discord.ext import commands as ext_commands

from utils.resolver import clan_autocomplete

from .commands.roster import roster
from .commands.round import round

_tag = app_commands.describe(tag="Clan tag or alias. Defaults to this server's linked clan.")
_ac = app_commands.autocomplete(tag=clan_autocomplete)


def _clan_opt(fn):
    return _ac(_tag(fn))


class cwl(ext_commands.Cog):
    """Clan War League commands."""

    def __init__(self, bot):
        self.bot = bot
        self.group = app_commands.Group(name="cwl", description="Clan War League roster and rounds")

        self.group.command(name="roster", description="Show the CWL season roster of clans")(_clan_opt(roster))
        self.group.command(name="round", description="Show the clan's current CWL round")(_clan_opt(round))

        bot.tree.add_command(self.group)

    async def cog_unload(self):
        self.bot.tree.remove_command("cwl")


async def setup(bot):
    await bot.add_cog(cwl(bot))
