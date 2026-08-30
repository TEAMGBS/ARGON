import discord
from discord import app_commands
from discord.ext import commands as ext_commands

from utils.resolver import clan_autocomplete

from .commands.boosts import boosts
from .commands.compo import compo
from .commands.donations import donations
from .commands.info import info
from .commands.search import search

# Shared "tag" option (with autocomplete of the guild's linked clans).
_tag = app_commands.describe(tag="Clan tag or alias. Defaults to this server's linked clan.")
_ac = app_commands.autocomplete(tag=clan_autocomplete)


def _clan_opt(fn):
    return _ac(_tag(fn))


class clan(ext_commands.Cog):
    """Clan overview commands."""

    def __init__(self, bot):
        self.bot = bot
        self.group = app_commands.Group(name="clan", description="Clan overview and stats")

        self.group.command(name="info", description="Show a clan's overview and details")(_clan_opt(info))
        self.group.command(name="compo", description="Show a clan's Town Hall composition")(_clan_opt(compo))
        self.group.command(name="donations", description="Show a clan's donation leaderboard")(_clan_opt(donations))
        self.group.command(name="boosts", description="Show active Super Troop boosts in a clan")(_clan_opt(boosts))
        self.group.command(name="search", description="Search clans by name")(
            app_commands.describe(name="Clan name to search for")(search)
        )

        bot.tree.add_command(self.group)

    async def cog_unload(self):
        self.bot.tree.remove_command("clan")


async def setup(bot):
    await bot.add_cog(clan(bot))
