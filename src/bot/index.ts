import 'reflect-metadata';
import { config } from 'dotenv';
config();

import { ClusterManager } from 'discord-hybrid-sharding';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';
import { logger } from '../util/logger.js';

/**
 * Entry point. Spawns one or more clusters via discord-hybrid-sharding, each of which runs main.ts.
 * For small bots a single cluster/shard is fine; the manager scales to many shards unchanged.
 */
function bootstrap() {
  const token = process.env.DISCORD_TOKEN;
  if (!token) {
    logger.error('DISCORD_TOKEN is not set. Copy .env.example to .env and fill it in.');
    process.exit(1);
  }

  const here = dirname(fileURLToPath(import.meta.url));
  // In dev (tsx) this file is .ts; compiled it's .js. Resolve main relative to this file.
  const isTs = import.meta.url.endsWith('.ts');
  const mainFile = resolve(here, isTs ? 'main.ts' : 'main.js');

  const totalShards = process.env.TOTAL_SHARDS === 'auto' ? 'auto' : Number(process.env.TOTAL_SHARDS || 1);
  const shardsPerClusters = Number(process.env.SHARDS_PER_CLUSTER || 8);

  const manager = new ClusterManager(mainFile, {
    token,
    totalShards,
    shardsPerClusters,
    mode: 'process',
    execArgv: isTs ? ['--import', 'tsx'] : []
  });

  manager.on('clusterCreate', (cluster) => logger.info(`Launched cluster #${cluster.id}.`));
  manager.spawn({ timeout: -1 }).catch((error) => {
    logger.error('Failed to spawn clusters:', error);
    process.exit(1);
  });
}

bootstrap();
