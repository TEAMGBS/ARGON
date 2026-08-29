import { ClusterClient, getInfo } from 'discord-hybrid-sharding';
import { Client as DiscordClient, GatewayIntentBits, Options, Partials } from 'discord.js';
import { Logger } from '../../util/logger.js';
import { CommandHandler } from './CommandHandler.js';
import { ListenerHandler } from './ListenerHandler.js';
import { Database } from './Database.js';
import { RedisService } from './RedisService.js';
import { Coc } from './Coc.js';
import { Resolver } from './Resolver.js';
import { SettingsProvider } from './SettingsProvider.js';
import { Scheduler } from './Scheduler.js';
import { initI18n } from './i18n.js';

/** The bot's central object: a discord.js Client extended with the bot's services and handlers. */
export class Client extends DiscordClient {
  public readonly log = new Logger('Client');
  public readonly cluster?: ClusterClient<DiscordClient>;

  public readonly db = new Database();
  public readonly redis = new RedisService();
  public readonly coc = new Coc();
  public readonly settings = new SettingsProvider(this.db);
  public readonly resolver = new Resolver(this);
  public readonly commandHandler = new CommandHandler(this);
  public readonly listenerHandler = new ListenerHandler(this);
  public readonly scheduler = new Scheduler(this);

  public constructor() {
    const sharded = Boolean(process.env.CLUSTER_MANAGER_MODE) || 'SHARD_LIST' in process.env;
    super({
      intents: [GatewayIntentBits.Guilds, GatewayIntentBits.GuildMembers],
      partials: [Partials.GuildMember, Partials.User, Partials.Channel],
      makeCache: Options.cacheWithLimits({
        ...Options.DefaultMakeCacheSettings,
        MessageManager: 0,
        PresenceManager: 0
      }),
      ...(sharded
        ? { shards: getInfo().SHARD_LIST, shardCount: getInfo().TOTAL_SHARDS }
        : {})
    });

    if (sharded) this.cluster = new ClusterClient(this);
  }

  /** Boot order: infra connections -> i18n -> handlers -> gateway login -> scheduler. */
  public async init(token: string): Promise<void> {
    await this.db.connect();
    await this.redis.connect();
    await this.coc.init();
    await this.settings.init();
    await initI18n();

    await this.commandHandler.loadAll();
    this.commandHandler.register();
    await this.listenerHandler.loadAll();

    await this.login(token);
    this.scheduler.start();
  }

  public async shutdown(): Promise<void> {
    this.scheduler.stop();
    await this.redis.disconnect().catch(() => null);
    await this.db.disconnect().catch(() => null);
    this.destroy();
  }
}
