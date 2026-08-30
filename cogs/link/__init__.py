import discord
from discord import app_commands
from discord.ext import commands as ext_commands

from .commands.add import add
from .commands.list_ import list_
from .commands.remove import remove
from .commands.verify import verify


class link(ext_commands.Cog):
    """Link Clash of Clans accounts to Discord."""

    def __init__(self, bot):
        self.bot = bot
        self.group = app_commands.Group(name="link", description="Link Clash of Clans accounts to Discord")

        self.group.command(name="add", description="Link a player tag to yourself or another user")(
            app_commands.describe(tag="Your CoC player tag (e.g. #2PP0)", user="Link on behalf of another user")(add)
        )
        self.group.command(name="list", description="List linked accounts")(
            app_commands.describe(user="User to list (defaults to you)")(list_)
        )
        self.group.command(name="remove", description="Unlink a player tag")(
            app_commands.describe(tag="The player tag to unlink")(remove)
        )
        self.group.command(name="verify", description="Verify ownership with the in-game API token")(
            app_commands.describe(
                tag="Your player tag",
                token="In-game API token (Settings → More Settings → API Token)",
            )(verify)
        )

        bot.tree.add_command(self.group)

    async def cog_unload(self):
        self.bot.tree.remove_command("link")


async def setup(bot):
    await bot.add_cog(link(bot))
