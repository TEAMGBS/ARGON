import { Collection, Db, Document, MongoClient } from 'mongodb';
import { Collections } from '../../entities/index.js';
import type {
  Alias,
  ClanSnapshot,
  ClanStore,
  Flag,
  GuildSettings,
  PlayerLink,
  Reminder,
  ReminderLog,
  UserInfo
} from '../../entities/index.js';
import { Logger } from '../../util/logger.js';

/** Thin MongoDB wrapper exposing typed collection getters and index setup. */
export class Database {
  private client!: MongoClient;
  private db!: Db;
  private readonly log = new Logger('Database');

  public async connect(): Promise<void> {
    const uri = process.env.MONGODB_URI || 'mongodb://localhost:27017';
    const dbName = process.env.MONGODB_DB_NAME || 'argon';
    this.client = new MongoClient(uri);
    await this.client.connect();
    this.db = this.client.db(dbName);
    await this.ensureIndexes();
    this.log.info(`Connected to MongoDB (${dbName}).`);
  }

  public async disconnect(): Promise<void> {
    await this.client?.close();
  }

  private async ensureIndexes(): Promise<void> {
    await this.guildSettings.createIndex({ guildId: 1 }, { unique: true });
    await this.clanStores.createIndex({ guildId: 1, tag: 1 }, { unique: true });
    await this.clanStores.createIndex({ tag: 1 });
    await this.playerLinks.createIndex({ userId: 1, tag: 1 }, { unique: true });
    await this.playerLinks.createIndex({ tag: 1 });
    await this.reminders.createIndex({ guildId: 1 });
    await this.reminderLogs.createIndex({ reminderId: 1, key: 1 }, { unique: true });
    await this.flags.createIndex({ guildId: 1, tag: 1 });
    await this.aliases.createIndex({ guildId: 1, name: 1 }, { unique: true });
    await this.clanSnapshots.createIndex({ guildId: 1, tag: 1 }, { unique: true });
  }

  private collection<T extends Document>(name: string): Collection<T> {
    return this.db.collection<T>(name);
  }

  public get guildSettings(): Collection<GuildSettings> {
    return this.collection<GuildSettings>(Collections.GUILD_SETTINGS);
  }
  public get clanStores(): Collection<ClanStore> {
    return this.collection<ClanStore>(Collections.CLAN_STORES);
  }
  public get playerLinks(): Collection<PlayerLink> {
    return this.collection<PlayerLink>(Collections.PLAYER_LINKS);
  }
  public get users(): Collection<UserInfo> {
    return this.collection<UserInfo>(Collections.USERS);
  }
  public get reminders(): Collection<Reminder> {
    return this.collection<Reminder>(Collections.REMINDERS);
  }
  public get reminderLogs(): Collection<ReminderLog> {
    return this.collection<ReminderLog>(Collections.REMINDER_LOGS);
  }
  public get flags(): Collection<Flag> {
    return this.collection<Flag>(Collections.FLAGS);
  }
  public get aliases(): Collection<Alias> {
    return this.collection<Alias>(Collections.ALIASES);
  }
  public get clanSnapshots(): Collection<ClanSnapshot> {
    return this.collection<ClanSnapshot>(Collections.CLAN_SNAPSHOTS);
  }
}
