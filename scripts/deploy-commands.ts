import 'reflect-metadata';
import { config } from 'dotenv';
config();

import { REST, Routes } from 'discord.js';
import { readdirp } from 'readdirp';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { dirname, resolve } from 'node:path';
import { Command } from '../src/bot/struct/Command.js';
import { logger } from '../src/util/logger.js';

/**
 * Registers slash commands with Discord. Uses DEV_GUILD_ID for instant, guild-scoped registration
 * during development, or registers globally when it's unset. Run with `npm run deploy`.
 */
async function main() {
  const token = process.env.DISCORD_TOKEN;
  const clientId = process.env.CLIENT_ID;
  if (!token || !clientId) {
    logger.error('DISCORD_TOKEN and CLIENT_ID must be set.');
    process.exit(1);
  }

  const here = dirname(fileURLToPath(import.meta.url));
  const commandsDir = resolve(here, '../src/bot/commands');

  const body: unknown[] = [];
  const isModule = (name: string) => /\.(js|ts)$/.test(name) && !name.endsWith('.d.ts');
  for await (const entry of readdirp(commandsDir, { fileFilter: (e) => isModule(e.basename), depth: 5, type: 'files' })) {
    const mod = await import(pathToFileURL(entry.fullPath).href);
    const Ctor = mod.default;
    if (typeof Ctor !== 'function') continue;
    const command: Command = new Ctor();
    if (!(command instanceof Command)) continue;
    body.push(command.builder().toJSON());
  }

  const rest = new REST({ version: '10' }).setToken(token);
  const guildId = process.env.DEV_GUILD_ID;

  if (guildId) {
    await rest.put(Routes.applicationGuildCommands(clientId, guildId), { body });
    logger.info(`Registered ${body.length} commands to guild ${guildId}.`);
  } else {
    await rest.put(Routes.applicationCommands(clientId), { body });
    logger.info(`Registered ${body.length} global commands (may take up to 1h to appear).`);
  }
}

main().catch((error) => {
  logger.error('Failed to deploy commands:', error);
  process.exit(1);
});
