"""Environment configuration for ARGON.

Every secret and setting is read from environment variables (put them in a local
`.env` file for development, or in Railway's Variables tab in production). Nothing
is hardcoded.
"""

import os

from dotenv import load_dotenv

# Load a local .env file if present (no-op in production where real env vars are set).
load_dotenv()

# ─── Discord ──────────────────────────────────────────────────────────────────
BOT_TOKEN = os.getenv("BOT_TOKEN")
# Optional: a server id to instantly (re)sync commands to while developing.
TEST_GUILD_ID = int(os.getenv("TEST_GUILD_ID", 0)) if os.getenv("TEST_GUILD_ID") else None
# Optional: your own Discord id (owner-only commands can check this).
BOT_DEV_ID = int(os.getenv("BOT_DEV", 0)) if os.getenv("BOT_DEV") else None

# ─── Clash of Clans API ───────────────────────────────────────────────────────
# Log in with your developer-site account and coc.py mints/rotates an IP-locked
# key for the current host automatically (works great on Railway's changing IPs).
COC_EMAIL = os.getenv("COC_EMAIL")
COC_PASSWORD = os.getenv("COC_PASSWORD")

# ─── Database (Supabase / Postgres) ───────────────────────────────────────────
# The Supabase connection string. Use the "Connection pooling" URI (port 6543)
# for hosted deployments. Railway's Postgres plugin exposes DATABASE_URL too.
DATABASE_URL = os.getenv("DATABASE_URL")

# ─── Cosmetics / behaviour ────────────────────────────────────────────────────
SUPPORT_SERVER = os.getenv("SUPPORT_SERVER", "https://discord.gg/")
# How often (seconds) the background loop checks war reminders and clan feeds.
POLL_INTERVAL_SECONDS = int(os.getenv("POLL_INTERVAL_SECONDS", 60))
