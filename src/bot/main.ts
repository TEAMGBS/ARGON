import 'reflect-metadata';
import { config } from 'dotenv';
config();

import { Client } from './struct/Client.js';
import { logger } from '../util/logger.js';

/** Per-cluster process bootstrap: build the Client and log in. */
const client = new Client();

async function start() {
  const token = process.env.DISCORD_TOKEN!;
  await client.init(token);
}

start().catch((error) => {
  logger.error('Fatal error during startup:', error);
  process.exit(1);
});

const shutdown = async (signal: string) => {
  logger.info(`Received ${signal}, shutting down…`);
  await client.shutdown();
  process.exit(0);
};

process.on('SIGINT', () => void shutdown('SIGINT'));
process.on('SIGTERM', () => void shutdown('SIGTERM'));
process.on('unhandledRejection', (reason) => logger.error('Unhandled rejection:', reason));
