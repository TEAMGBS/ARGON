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
- A **Clash of Clans API token** — https://developer.clashofclans.com
  (keys are IP-locked; alternatively set `CLASH_API_EMAIL` / `CLASH_API_PASSWORD` and the bot mints
  keys for the current host automatically)

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
