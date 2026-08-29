import { createClient, RedisClientType } from 'redis';
import { Logger } from '../../util/logger.js';

/** Thin Redis wrapper for caching and cross-shard coordination. Swappable behind this interface. */
export class RedisService {
  public client: RedisClientType;
  private readonly log = new Logger('Redis');
  private connected = false;

  public constructor() {
    this.client = createClient({ url: process.env.REDIS_URL || 'redis://localhost:6379' });
    this.client.on('error', (err) => this.log.error(err));
  }

  public async connect(): Promise<void> {
    if (this.connected) return;
    await this.client.connect();
    this.connected = true;
    this.log.info('Connected to Redis.');
  }

  public async disconnect(): Promise<void> {
    if (!this.connected) return;
    await this.client.quit();
    this.connected = false;
  }

  /** Get a JSON value, or null if missing/expired. */
  public async getJSON<T>(key: string): Promise<T | null> {
    const raw = await this.client.get(key);
    return raw ? (JSON.parse(raw) as T) : null;
  }

  /** Set a JSON value with an optional TTL (seconds). */
  public async setJSON(key: string, value: unknown, ttlSeconds?: number): Promise<void> {
    const raw = JSON.stringify(value);
    if (ttlSeconds) await this.client.set(key, raw, { EX: ttlSeconds });
    else await this.client.set(key, raw);
  }

  /** Best-effort distributed lock — returns true if the lock was acquired. */
  public async acquireLock(key: string, ttlSeconds: number): Promise<boolean> {
    const res = await this.client.set(key, '1', { NX: true, EX: ttlSeconds });
    return res === 'OK';
  }
}
