import type { GuildSettings } from '../../entities/index.js';
import { DEFAULT_COLOR } from '../../util/constants.js';
import type { Database } from './Database.js';

/** Caches per-guild settings (color, timezone, locale) in memory with a write-through to Mongo. */
export class SettingsProvider {
  private cache = new Map<string, GuildSettings>();

  public constructor(private readonly db: Database) {}

  public async init(): Promise<void> {
    const all = await this.db.guildSettings.find({}).toArray();
    for (const doc of all) this.cache.set(doc.guildId, doc);
  }

  public get(guildId: string): GuildSettings | undefined {
    return this.cache.get(guildId);
  }

  /** Resolved embed color for a guild: guild override -> env default -> hardcoded default. */
  public color(guildId: string | null): number {
    const hex = (guildId && this.cache.get(guildId)?.color) || process.env.EMBED_COLOR;
    if (hex) {
      const parsed = parseInt(hex.replace(/^#/, ''), 16);
      if (!Number.isNaN(parsed)) return parsed;
    }
    return DEFAULT_COLOR;
  }

  public timezone(guildId: string | null): string {
    return (guildId && this.cache.get(guildId)?.timezone) || 'UTC';
  }

  public async set(guildId: string, patch: Partial<GuildSettings>): Promise<void> {
    const now = new Date();
    await this.db.guildSettings.updateOne(
      { guildId },
      { $set: { ...patch, guildId, updatedAt: now }, $setOnInsert: { createdAt: now } },
      { upsert: true }
    );
    const doc = await this.db.guildSettings.findOne({ guildId });
    if (doc) this.cache.set(guildId, doc);
  }
}
