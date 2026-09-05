import discord
from discord import app_commands
from discord.ext import commands as ext_commands

from utils.resolver import clan_autocomplete

from .commands.info import handle as war_info

_WAR_TYPE_CHOICES = [
    app_commands.Choice(name="Normal", value="normal"),
    app_commands.Choice(name="CWL", value="cwl"),
    app_commands.Choice(name="Friendly", value="friendly"),
]


class war(ext_commands.Cog):
    """On-demand clan war information."""

    def __init__(self, bot):
        self.bot = bot
        self.group = app_commands.Group(name="war", description="Clan war info", guild_only=True)

        self.group.command(name="info", description="Show a clan's current war board")(
            app_commands.describe(
                clan="An alliance clan (defaults to the first one added)",
                type="Only show if the current war is this type",
            )(
                app_commands.autocomplete(clan=clan_autocomplete)(
                    app_commands.choices(type=_WAR_TYPE_CHOICES)(war_info)
                )
            )
        )

        bot.tree.add_command(self.group)

    async def cog_unload(self):
        self.bot.tree.remove_command("war")


async def setup(bot):
    await bot.add_cog(war(bot))
