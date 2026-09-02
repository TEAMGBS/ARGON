# ARGON

A simple **Clash of Clans Discord bot** written in **Python** (discord.py + coc.py) with a
**Supabase / Postgres** database.

> Kept intentionally minimal for now: account linking, clan logs, and war reminders. More features
> will be added back over time.

## Commands

| Group | Commands | What it does |
| --- | --- | --- |
| `/link` | `add` `list` `remove` `verify` | Link Clash of Clans accounts to a Discord user |
| `/setup` | `clan` `remove` `list` `log` | Link clans to the server and set up their logs |
| `/reminders` | `add` `list` `remove` | War reminders for members who still have attacks |

Background services (run automatically):

- **Clan logs / feed** — member join/leave and donation logs, posted to the channels set with
  `/setup log`.
- **War reminders** — fired by the scheduler for members who have not used their attacks.

## Project layout

```
config.py                 # env vars
main.py                   # connect DB, log into CoC, load cogs, start bot
database/db.py + schema.sql
utils/                    # tags, embeds, emojis, helpers, resolver
cogs/link/                # /link
cogs/setup/               # /setup (clan linking + logs)
cogs/reminders/           # /reminders + the background scheduler (tasks.py)
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
python main.py            # creates the tables on first run, then starts the bot
```

Deploy on Railway by pointing it at this repo (it reads `railway.json`, start: `python main.py`) and
setting the variables above.

## Roadmap

Player, clan, war, CWL, legend, flags, export and the emoji tools were part of an earlier build and
will be reintroduced gradually. The one-cog-per-feature layout is the extension point for them.

## License

MIT
