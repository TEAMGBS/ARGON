"""ARGON, a ClashPerk-style Clash of Clans Discord bot.

Boot order: connect to the database, log into the Clash of Clans API (which mints
an IP-locked key for this host automatically), load every cog, then start the bot
and sync slash commands globally.
"""

import asyncio
import traceback

import coc
import discord
from discord import app_commands
from discord.ext import commands, tasks

from config import BOT_TOKEN, COC_EMAIL, COC_PASSWORD, DATABASE_URL, TEST_GUILD_ID
from database.db import close_pool, init_pool

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Kept intentionally minimal for now: account linking, clan logs, and war
# reminders. More cogs will be added back as the bot grows.
COGS = [
    "cogs.link",
    "cogs.alliance",
    "cogs.setup",
    "cogs.reminders",
    "cogs.emoji",
    "cogs.ranked",
]


@tasks.loop(seconds=30)
async def rotate_presence():
    """Keep the bot's presence looking alive."""
    total = sum(g.member_count or 0 for g in bot.guilds)
    try:
        await bot.change_presence(
            activity=discord.Activity(type=discord.ActivityType.watching, name=f"{total:,} members • /help")
        )
    except Exception:
        pass


@rotate_presence.before_loop
async def _before_presence():
    await bot.wait_until_ready()


@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")
    print(f"✅ Connected to {len(bot.guilds)} guild(s)")
    if not rotate_presence.is_running():
        rotate_presence.start()
    try:
        # Sync commands globally only. Copying globals into the test guild as well
        # makes every command show up twice there (once global, once guild-scoped),
        # so instead we clear any guild-scoped commands the test guild still has.
        # This is self-healing: leaving TEST_GUILD_ID set is harmless, and any
        # existing duplicates clear on the next boot.
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} global command(s).")
        if TEST_GUILD_ID:
            guild = discord.Object(id=TEST_GUILD_ID)
            bot.tree.clear_commands(guild=guild)
            await bot.tree.sync(guild=guild)
            print(f"✅ Cleared guild-scoped commands in test guild {TEST_GUILD_ID}; using global only.")
    except Exception:
        print(f"❌ Failed to sync commands:\n{traceback.format_exc()}")


@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    cmd = interaction.command.name if interaction.command else "?"
    print(f"❌ Slash command error in /{cmd}:")
    traceback.print_exc()
    try:
        message = f"❌ Something went wrong: `{error}`"
        if interaction.response.is_done():
            await interaction.followup.send(message, ephemeral=True)
        else:
            await interaction.response.send_message(message, ephemeral=True)
    except Exception:
        pass


async def main():
    # 1) Validate required config early with clear messages.
    missing = [
        name
        for name, value in {
            "BOT_TOKEN": BOT_TOKEN,
            "COC_EMAIL": COC_EMAIL,
            "COC_PASSWORD": COC_PASSWORD,
            "DATABASE_URL": DATABASE_URL,
        }.items()
        if not value
    ]
    if missing:
        print(f"❌ Missing required environment variables: {', '.join(missing)}")
        return

    # 2) Database (Supabase / Postgres).
    print("⏳ Connecting to database...")
    try:
        await init_pool()
        print("✅ Database connected.")
    except Exception:
        print(f"❌ Database connection failed:\n{traceback.format_exc()}")
        return

    # 3) Clash of Clans API, email/password login mints an IP-locked key for
    #    this host and re-issues it when the IP changes (Railway-friendly).
    print("⏳ Logging into the Clash of Clans API...")
    try:
        coc_client = coc.Client(key_names="argon-bot", raw_attribute=True)
        await coc_client.login(COC_EMAIL, COC_PASSWORD)
        bot.coc_client = coc_client
        print("✅ Clash of Clans API connected.")
    except Exception:
        print(f"❌ Clash of Clans API login failed:\n{traceback.format_exc()}")
        await close_pool()
        return

    # 4) Load cogs.
    for cog in COGS:
        try:
            await bot.load_extension(cog)
            print(f"✅ Loaded cog: {cog}")
        except Exception:
            print(f"❌ Failed to load cog '{cog}':\n{traceback.format_exc()}")

    # 5) Start the gateway connection.
    print("⏳ Starting bot...")
    try:
        await bot.start(BOT_TOKEN)
    finally:
        await bot.coc_client.close()
        await close_pool()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Shutting down.")
