# ARGON

A feature-rich **Clash of Clans Discord bot** — a ClashPerk-style bot written in **Python**
(discord.py + coc.py) with a **Supabase / Postgres** database.

> An original reimplementation of ClashPerk's core feature set. Structured like the omega bot:
> `config.py`, a `database/` layer with a single idempotent `schema.sql`, and one cog package per
> feature area.

## Commands (42)

| Group | Commands |
| --- | --- |
| `/player` | `info` `units` `army` `rushed` `upgrades` |
| `/clan` | `info` `compo` `donations` `boosts` `search` |
| `/war` | `info` `log` `remaining` `lineup` |
| `/cwl` | `roster` `round` |
| `/legend` | — |
| `/link` | `add` `list` `remove` `verify` |
| `/setup` | `clan` `remove` `list` `log` |
| `/alias` | `add` `remove` `list` |
| `/reminders` | `add` `list` `remove` |
| `/flag` | `add` `remove` `list` |
| `/export` | `members` (CSV) |
| top-level | `/config` `/profile` `/timezone` `/help` `/ping` `/invite` `/status` |

Background services: a **war-reminder scheduler** and a **clan-feed poller** (member join/leave and
donation logs) that diff live clan state against Postgres snapshots and post to configured channels.

## Project layout

```
config.py                 # env vars
main.py                   # entry: connect DB, log into CoC, load cogs, start bot
database/
  db.py                   # asyncpg pool + applies schema.sql
  schema.sql              # the whole data model (idempotent CREATE TABLE IF NOT EXISTS)
utils/                    # tags, embeds, emojis, helpers, resolver (shared code)
cogs/<feature>/
  __init__.py             # the Cog: builds the app_commands group + setup()
  commands/<name>.py      # one file per command
  tasks.py                # (reminders) the background scheduler
```

Adding a command = add a file under a cog's `commands/` and wire one line in that cog's
`__init__.py`.

## Prerequisites

- **Python 3.11+**
- A **Discord bot token** + application — https://discord.com/developers/applications
- A **Clash of Clans developer account** — https://developer.clashofclans.com
- A **Supabase** project (free tier is fine) — https://supabase.com

### Clash of Clans API: just your email + password

Set `COC_EMAIL` and `COC_PASSWORD` (your developer-site login). On startup coc.py logs in, detects
this host's outbound IP, and **creates/rotates an IP-locked API key automatically** — so hosting on
Railway (where the IP can change on redeploy) just works, with no manual key creation.

## Setup (local)

```bash
git clone <this-repo> && cd argon
cp .env.example .env         # then fill in the values
pip install -r requirements.txt
python main.py               # creates the tables on first run, then starts the bot
```

The tables are created automatically from `database/schema.sql` the first time the bot connects.

## Deploying on Railway

1. **New Project → Deploy from GitHub repo** and pick this repo. Railway reads `railway.json`
   (start: `python main.py`) and installs `requirements.txt` automatically.
2. On the **service → Variables**, add:

   | Variable | Value |
   | --- | --- |
   | `BOT_TOKEN` | your Discord bot token |
   | `COC_EMAIL` | your developer.clashofclans.com email |
   | `COC_PASSWORD` | your developer.clashofclans.com password |
   | `DATABASE_URL` | your Supabase connection string (see below) |
   | `TEST_GUILD_ID` | *(optional)* a server id for instant command sync |

3. **Supabase connection string**: Supabase dashboard → *Project Settings → Database →
   Connection string → "Connection pooling"* (the URI on port **6543**). It looks like:
   `postgresql://postgres.<ref>:<password>@aws-0-<region>.pooler.supabase.com:6543/postgres`
   Paste that as `DATABASE_URL`. (The bot disables asyncpg's prepared-statement cache so the
   Supabase pooler works out of the box.)

That's it — no manual API-key creation, and redeploys that change Railway's IP are handled for you.

## Roadmap

The remaining ClashPerk commands (`summary-*`, `leaderboard-*`, `capital-*`, `clan-games`, full
history/legend-day tracking, roster management, Google-Sheets exports) are intentionally left out of
this MVP. The one-file-per-command layout above is the extension point for them.

## License

MIT
