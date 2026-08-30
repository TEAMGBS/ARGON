import discord
from discord import app_commands
from discord.ext import commands as ext_commands

from utils.resolver import clan_autocomplete

from .commands.info import info
from .commands.lineup import lineup
from .commands.log import log
from .commands.remaining import remaining

_tag = app_commands.describe(tag="Clan tag or alias. Defaults to this server's linked clan.")
_ac = app_commands.autocomplete(tag=clan_autocomplete)


def _clan_opt(fn):
    return _ac(_tag(fn))


class war(ext_commands.Cog):
    """War status commands."""

    def __init__(self, bot):
        self.bot = bot
        self.group = app_commands.Group(name="war", description="Current war and war log")

        self.group.command(name="info", description="Show a clan's current war")(_clan_opt(info))
        self.group.command(name="log", description="Show a clan's recent war results")(_clan_opt(log))
        self.group.command(name="remaining", description="Show remaining war attacks")(_clan_opt(remaining))
        self.group.command(name="lineup", description="Show the war lineup for both sides")(_clan_opt(lineup))

        bot.tree.add_command(self.group)

    async def cog_unload(self):
        self.bot.tree.remove_command("war")


async def setup(bot):
    await bot.add_cog(war(bot))
