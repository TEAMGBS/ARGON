import discord
from discord import app_commands
from discord.ext import commands as ext_commands

from utils.embeds import base_embed, error_embed
from utils.emojis import E_TROPHY
from utils.resolver import resolve_player


class legend(ext_commands.Cog):
    """Legend League stats."""

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="legend", description="Show a player's Legend League stats")
    @app_commands.describe(
        tag="A CoC player tag. Defaults to your linked account.",
        user="Look up another Discord user's linked account.",
    )
    async def legend(self, interaction: discord.Interaction, tag: str = None, user: discord.User = None):
        await interaction.response.defer()
        try:
            player = await resolve_player(interaction, tag, user)
        except ValueError as err:
            await interaction.followup.send(embed=error_embed(str(err)))
            return

        stats = player.legend_statistics
        embed = await base_embed(interaction, title=f"{player.name} ({player.tag}), Legend League")

        league_name = player.league.name if player.league else "Unranked"
        if league_name != "Legend League" and stats is None:
            embed.description = f"This player is currently in **{league_name}**, not Legend League."
            embed.add_field(name="Trophies", value=f"{E_TROPHY} {player.trophies}", inline=True)
            await interaction.followup.send(embed=embed)
            return

        embed.add_field(name="Current Trophies", value=f"{E_TROPHY} {player.trophies}", inline=True)
        if stats is not None:
            best = stats.best_season
            if best is not None:
                embed.add_field(name="Best Season", value=f"{E_TROPHY} {best.trophies} (#{best.rank})", inline=True)
            if stats.current_season is not None:
                embed.add_field(name="Current Season", value=f"{E_TROPHY} {stats.current_season.trophies}", inline=True)

        embed.set_footer(text="Per-day attack tracking is a roadmap feature (needs stored snapshots).")
        await interaction.followup.send(embed=embed)


async def setup(bot):
    await bot.add_cog(legend(bot))
