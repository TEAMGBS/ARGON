import time
from zoneinfo import ZoneInfo, available_timezones

import discord
from discord import app_commands
from discord.ext import commands as ext_commands

from config import SUPPORT_SERVER
from database.db import get_pool
from utils.embeds import base_embed, error_embed, success_embed
from utils.emojis import E_CORRECT, E_TROPHY, E_TOWNHALL
from utils.resolver import all_tags_for_user

_ALL_TZ = sorted(available_timezones())


class util(ext_commands.Cog):
    """Utility and information commands."""

    def __init__(self, bot):
        self.bot = bot
        self.start_time = time.time()

    @app_commands.command(name="ping", description="Check the bot latency")
    async def ping(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"🏓 Pong! Gateway `{round(self.bot.latency * 1000)}ms`")

    @app_commands.command(name="invite", description="Get the bot invite and support links")
    async def invite(self, interaction: discord.Interaction):
        perms = discord.Permissions(
            view_channel=True, send_messages=True, embed_links=True, manage_roles=True, manage_webhooks=True
        )
        url = discord.utils.oauth_url(self.bot.user.id, permissions=perms, scopes=("bot", "applications.commands"))
        embed = await base_embed(interaction, title="Invite ARGON")
        embed.description = f"• [Add me to your server]({url})\n• [Support server]({SUPPORT_SERVER})"
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="status", description="Show bot status and uptime")
    async def status(self, interaction: discord.Interaction):
        up = int(time.time() - self.start_time)
        days, rem = divmod(up, 86400)
        hours, rem = divmod(rem, 3600)
        minutes = rem // 60
        embed = await base_embed(interaction, title="ARGON, Status")
        embed.add_field(name="Uptime", value=f"{days}d {hours}h {minutes}m", inline=True)
        embed.add_field(name="Guilds", value=str(len(self.bot.guilds)), inline=True)
        embed.add_field(name="Gateway", value=f"{round(self.bot.latency * 1000)}ms", inline=True)
        embed.add_field(name="discord.py", value=discord.__version__, inline=True)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="help", description="List available commands")
    async def help(self, interaction: discord.Interaction):
        embed = await base_embed(interaction, title="ARGON, Commands")
        embed.description = "A ClashPerk-style Clash of Clans bot. Type `/` and pick a command group."
        for cmd in sorted(self.bot.tree.get_commands(), key=lambda c: c.name):
            if isinstance(cmd, app_commands.Group):
                subs = " ".join(f"`{s.name}`" for s in cmd.commands)
                embed.add_field(name=f"/{cmd.name}", value=subs or "-", inline=False)
            else:
                embed.add_field(name=f"/{cmd.name}", value=cmd.description or "-", inline=True)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="profile", description="Show a member's linked accounts profile")
    @app_commands.describe(user="User to view (defaults to you)")
    async def profile(self, interaction: discord.Interaction, user: discord.User = None):
        await interaction.response.defer()
        target = user or interaction.user
        pool = await get_pool()
        rows = await all_tags_for_user(pool, target.id)
        if not rows:
            await interaction.followup.send(embed=error_embed(f"{target.mention} has no linked accounts."))
            return

        lines = []
        for row in rows:
            try:
                p = await self.bot.coc_client.get_player(row["tag"])
            except Exception:
                continue
            mark = E_CORRECT if row["verified"] else ""
            clan = f" • {p.clan.name}" if p.clan else ""
            lines.append(f"{mark} {E_TOWNHALL}TH{p.town_hall} **{p.name}** ({p.tag}), {E_TROPHY} {p.trophies}{clan}")

        embed = await base_embed(interaction, title=f"{target.display_name}, Profile")
        embed.description = "\n".join(lines)[:4000] or "_Could not load any accounts._"
        embed.set_thumbnail(url=target.display_avatar.url)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="timezone", description="Set your timezone (e.g. Europe/London)")
    @app_commands.describe(zone="IANA timezone id, e.g. America/New_York")
    async def timezone(self, interaction: discord.Interaction, zone: str):
        if zone not in _ALL_TZ:
            await interaction.response.send_message(
                embed=error_embed(f"`{zone}` is not a valid timezone id."), ephemeral=True
            )
            return
        from datetime import datetime

        pool = await get_pool()
        await pool.execute(
            """INSERT INTO user_settings (discord_id, timezone) VALUES ($1, $2)
               ON CONFLICT (discord_id) DO UPDATE SET timezone = EXCLUDED.timezone, updated_at = NOW()""",
            interaction.user.id,
            zone,
        )
        now = datetime.now(ZoneInfo(zone)).strftime("%H:%M")
        await interaction.response.send_message(
            embed=success_embed(f"Timezone set to `{zone}` (local time {now})."), ephemeral=True
        )

    @timezone.autocomplete("zone")
    async def _tz_autocomplete(self, interaction: discord.Interaction, current: str):
        q = current.lower()
        matches = [z for z in _ALL_TZ if q in z.lower()][:25]
        return [app_commands.Choice(name=z, value=z) for z in matches]


async def setup(bot):
    await bot.add_cog(util(bot))
