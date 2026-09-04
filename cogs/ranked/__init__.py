import discord
from discord import app_commands
from discord.ext import commands as ext_commands

from .autocomplete import tag_autocomplete
from .commands.card import handle as card_player
from .commands.list import handle as list_tracked
from .commands.setup import handle as track_setup
from .commands.track import handle as track_player
from .commands.untrack import handle as untrack_player


class ranked(ext_commands.Cog):
    """Legend League tracking: notify on attacks/defenses and render battle-log cards."""

    def __init__(self, bot):
        self.bot = bot
        # No default_permissions on the group: card-player is public, the rest
        # check Manage Server themselves (see commands/_guard.py).
        self.group = app_commands.Group(name="ranked", description="Legend League tracking", guild_only=True)

        self.group.command(name="track-setup", description="Set the channel for legend attack/defense notifications")(
            app_commands.describe(channel="Channel to post legend notifications in")(track_setup)
        )
        self.group.command(name="track-player", description="Track a player's legend attacks and defenses")(
            app_commands.describe(tag="Player tag, e.g. #ABC123")(
                app_commands.autocomplete(tag=tag_autocomplete)(track_player)
            )
        )
        self.group.command(name="untrack-player", description="Stop tracking a player")(
            app_commands.describe(tag="Player tag")(app_commands.autocomplete(tag=tag_autocomplete)(untrack_player))
        )
        self.group.command(name="list", description="List the players this server is tracking")(list_tracked)
        self.group.command(name="card-player", description="Show a player's legend battle-log card")(
            app_commands.describe(tag="Player tag")(app_commands.autocomplete(tag=tag_autocomplete)(card_player))
        )

        bot.tree.add_command(self.group)

    async def cog_unload(self):
        self.bot.tree.remove_command("ranked")


async def setup(bot):
    from .tracker import RankedTracker

    await bot.add_cog(ranked(bot))
    await bot.add_cog(RankedTracker(bot))
