# ARGON

A feature-rich **Clash of Clans Discord bot** — an open, extensible replica of
[ClashPerk](https://docs.clashperk.com), built to match its architecture: TypeScript,
discord.js v14, MongoDB, Redis and the official Clash of Clans API.

> This is an original reimplementation of ClashPerk's design and core feature set (ClashPerk is
> MIT-licensed). It is not a verbatim copy of the upstream codebase.

## Features (MVP)

Slash commands, grouped like the ClashPerk docs:

| Category | Commands |
| --- | --- |
| **Player** | `/player`, `/units`, `/army`, `/rushed`, `/upgrades` |
| **Clan** | `/clan`, `/compo`, `/donations`, `/boosts`, `/search` |
| **War** | `/war`, `/warlog`, `/remaining`, `/lineup` |
| **CWL** | `/cwl` (roster / round) |
| **Legend** | `/legend` (attacks / summary) |
| **Links** | `/link`, `/verify`, `/profile`, `/timezone` |
| **Setup** | `/setup`, `/config`, `/alias` |
| **Reminders** | `/reminders` (war reminders via the scheduler) |
| **Flags** | `/flag` |
| **Utility** | `/help`, `/invite`, `/ping`, `/status` |
| **Export** | `/export-members` (CSV) |

Background services: a **war-reminder scheduler** and a **clan-feed poller** (member join/leave and
donation logs) that diff live clan state against MongoDB snapshots and post to configured channels.

## Architecture

```
src/
  bot/
    index.ts               # entry — discord-hybrid-sharding cluster manager
    main.ts                # per-shard bootstrap -> Client.init()
    struct/                # Client, CommandHandler, ListenerHandler, Command/Listener base,
                           # Database, RedisService, Coc, Resolver, SettingsProvider, i18n, Scheduler
    commands/<category>/   # one file per command (auto-loaded)
    listeners/<source>/    # gateway events (auto-loaded)
  util/                    # constants, emojis, helpers, embeds
  entities/                # MongoDB document interfaces + collection names
locales/en.json            # i18next strings
scripts/deploy-commands.ts # register slash commands with Discord
```

The command framework auto-loads every file under `src/bot/commands/`, so **adding a command is
adding one file** — see [Adding a command](#adding-a-command).

## Prerequisites

- **Node.js >= 22**
- **MongoDB** and **Redis** (a `docker-compose.yml` is provided for both)
- A **Discord bot token** + application id — https://discord.com/developers/applications
- A **Clash of Clans developer account** — https://developer.clashofclans.com

### Clash of Clans API: just use your email + password

You do **not** need to create an API key by hand. Set `CLASH_API_EMAIL` and `CLASH_API_PASSWORD`
(your developer-site login) and on every startup the bot:

1. logs in to the developer site,
2. detects the outbound IP of the machine it's running on, and
3. creates or rotates an **IP-locked API key** for that exact IP automatically.

This is why it's the right choice for Railway and other hosts where the IP can change between
deploys — the key follows the new IP with zero manual steps. (Static `CLASH_API_TOKENS` are still
supported for fixed-IP boxes.)

## Setup

```bash
git clone <this-repo>
cd argon
cp .env.example .env        # then fill in the values
npm install

# start Mongo + Redis locally
docker compose up -d mongo redis

# register slash commands (uses DEV_GUILD_ID if set, else global)
npm run deploy

# run in watch mode
npm run dev
```

Production:

```bash
npm run build
npm start
# or the whole stack:
docker compose up -d --build
```

## Deploying on Railway

1. **New Project → Deploy from GitHub repo** and pick this repo. Railway reads `railway.json`
   (build: `npm run build`, start: `npm start`) automatically.
2. **Add a MongoDB database** and **a Redis database** to the project (Railway → *New* → *Database*).
   They expose `MONGO_URL` and `REDIS_URL`; the bot reads those names automatically, so you don't have
   to wire them up manually. (If you use Railway's variable references instead, set `MONGODB_URI`
   and `REDIS_URL`.)
3. On the **bot service → Variables**, add:

   | Variable | Value |
   | --- | --- |
   | `DISCORD_TOKEN` | your bot token |
   | `CLIENT_ID` | your application id |
   | `CLASH_API_EMAIL` | your developer.clashofclans.com email |
   | `CLASH_API_PASSWORD` | your developer.clashofclans.com password |
   | `DEV_GUILD_ID` | *(optional)* a server id for instant command registration |

   You do **not** need `CLASH_API_TOKENS` — the email/password login mints an IP-locked key for
   Railway's IP on each deploy (see above).
4. **Register the slash commands once** (Railway's shell, or locally with the same env):
   `npm run deploy`. After that, every deploy just runs the bot.

That's the whole setup — no manual API-key creation, and redeploys that change Railway's IP are
handled for you.

## Adding a command

Create `src/bot/commands/<category>/<name>.ts`:

```ts
import { ChatInputCommandInteraction, SlashCommandBuilder } from 'discord.js';
import { Command } from '../../struct/Command.js';

export default class PingCommand extends Command {
  public constructor() {
    super('ping', { category: 'util', description: 'Check the bot latency.' });
  }

  public builder() {
    return new SlashCommandBuilder().setName('ping').setDescription('Check the bot latency.');
  }

  public async exec(interaction: ChatInputCommandInteraction) {
    await interaction.reply(`Pong! ${this.client.ws.ping}ms`);
  }
}
```

Run `npm run deploy` to register it, then `npm run dev`. That's it — the handler discovers it.

## Roadmap

The remaining ClashPerk commands (`summary-*`, `leaderboard-*`, `capital-*`, `clan-games`, `history`,
`roster-*`, the full `cwl-*` set, Google-Sheets exports, and the ClickHouse/Kafka analytics pipeline)
are intentionally left as scaffolding. The category folders and the one-file-per-command pattern above
are the extension points for them.

## License

MIT
