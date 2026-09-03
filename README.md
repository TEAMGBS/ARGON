# ARGON

A **Clash of Clans Discord bot** written in **Python** (discord.py + coc.py) with a
**Supabase / Postgres** database.

> Minimal and growing. Admins add clans to the server, then set up logs and reminders for them.

## How it works

1. An admin adds a clan to the server with **`/alliance add-clan`**.
2. Once a clan is added, they can configure **logs** (`/setup log`) and **reminders**
   (`/reminders create`) for it.
3. Members link their own Clash of Clans accounts with **`/link`**.

## Commands

| Group | Commands | What it does |
| --- | --- | --- |
| `/alliance` | `add-clan` `remove-clan` `show-clans` `info-clans` | Manage the clans in this server (admin) |
| `/setup` | `log` | Enable a member / donation / feed log for a clan in a channel (admin) |
| `/reminders` | `create` `list` `delete` | Interactive reminder config for a clan (admin) |
| `/link` | `add` `list` `remove` `verify` | Link Clash of Clans accounts to a Discord user |

`/reminders create` opens an interactive panel (buttons, selects, modals) to pick the reminder type
(war / capital / clan games), the timings, member filters (Town Hall, role, remaining attacks) and a
custom message, then saves it with a short id.

Background services run automatically: clan **feed/logs** (member join/leave + donations) and **war
reminders** fired at the configured timings. Capital and Clan Games reminders can be configured now;
their firing is a roadmap item.

## Project layout

```
config.py                 # env vars
main.py                   # connect DB, log into CoC, load cogs, start bot
database/
  db.py                   # asyncpg pool + applies schema.sql
  clans.py                # clan (alliance) data access
  reminders.py            # reminder data access
  schema.sql              # the data model (idempotent, with a guarded migration)
utils/                    # tags, embeds, emojis, helpers, resolver
cogs/link/                # /link
cogs/alliance/            # /alliance (clan management)
cogs/setup/               # /setup log
cogs/reminders/           # /reminders + the interactive UI + background scheduler
```

## Environment variables

| Variable | Value |
| --- | --- |
| `BOT_TOKEN` | Discord bot token |
| `COC_EMAIL` / `COC_PASSWORD` | developer.clashofclans.com login (mints an IP-locked key automatically) |
| `DATABASE_URL` | Supabase connection-pooling URI (port 6543) |
| `TEST_GUILD_ID` | optional, for instant command sync while developing |

## Run

```bash
pip install -r requirements.txt
cp .env.example .env      # then fill in the values
python main.py            # creates/migrates the tables on first run, then starts the bot
```

Deploy on Railway by pointing it at this repo (it reads `railway.json`, start: `python main.py`).

## License

MIT
