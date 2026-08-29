import { Client as CocClient } from 'clashofclans.js';
import { normalizeTag } from '../../util/helper.js';
import { Logger } from '../../util/logger.js';

/**
 * Wrapper around `clashofclans.js`. Supports either static IP-locked API tokens
 * (CLASH_API_TOKENS) or an email/password login that mints keys for the current host.
 */
export class Coc {
  public readonly client: CocClient;
  private readonly log = new Logger('Coc');
  private ready = false;

  public constructor() {
    this.client = new CocClient({ cache: true, retryLimit: 2 });
  }

  public async init(): Promise<void> {
    if (this.ready) return;
    const tokens = (process.env.CLASH_API_TOKENS || '')
      .split(',')
      .map((t) => t.trim())
      .filter(Boolean);

    if (tokens.length) {
      this.client.setKeys(tokens);
      this.ready = true;
      this.log.info(`Initialized CoC client with ${tokens.length} static token(s).`);
      return;
    }

    const email = process.env.CLASH_API_EMAIL;
    const password = process.env.CLASH_API_PASSWORD;
    if (email && password) {
      await this.client.login({ email, password, keyName: 'argon-bot' });
      this.ready = true;
      this.log.info('Initialized CoC client via email/password login.');
      return;
    }

    throw new Error('No Clash of Clans credentials set (CLASH_API_TOKENS or CLASH_API_EMAIL/PASSWORD).');
  }

  /** Fetch a player by tag; returns null on 404/errors. */
  public async getPlayer(tag: string) {
    try {
      return await this.client.getPlayer(normalizeTag(tag));
    } catch (error) {
      this.log.debug(`getPlayer(${tag}) failed:`, (error as Error).message);
      return null;
    }
  }

  /** Fetch a clan by tag; returns null on 404/errors. */
  public async getClan(tag: string) {
    try {
      return await this.client.getClan(normalizeTag(tag));
    } catch (error) {
      this.log.debug(`getClan(${tag}) failed:`, (error as Error).message);
      return null;
    }
  }

  /** Current war for a clan (regular). Returns null if not in war / private log. */
  public async getCurrentWar(tag: string) {
    try {
      return await this.client.getCurrentWar(normalizeTag(tag));
    } catch (error) {
      this.log.debug(`getCurrentWar(${tag}) failed:`, (error as Error).message);
      return null;
    }
  }

  public async getWarLog(tag: string) {
    try {
      return await this.client.getClanWarLog(normalizeTag(tag));
    } catch (error) {
      this.log.debug(`getWarLog(${tag}) failed:`, (error as Error).message);
      return null;
    }
  }

  /** Current CWL group for a clan. Returns null when not in a CWL season. */
  public async getCwlGroup(tag: string) {
    try {
      return await this.client.getClanWarLeagueGroup(normalizeTag(tag));
    } catch (error) {
      this.log.debug(`getCwlGroup(${tag}) failed:`, (error as Error).message);
      return null;
    }
  }

  /** Verify a player token issued in-game (Settings -> More -> API Token). */
  public async verifyPlayerToken(tag: string, token: string): Promise<boolean> {
    try {
      return await this.client.verifyPlayerToken(normalizeTag(tag), token);
    } catch (error) {
      this.log.debug(`verifyPlayerToken(${tag}) failed:`, (error as Error).message);
      return false;
    }
  }

  /** Search clans by name (used by /search). */
  public async searchClans(name: string, limit = 10) {
    try {
      return await this.client.getClans({ name, limit });
    } catch (error) {
      this.log.debug(`searchClans(${name}) failed:`, (error as Error).message);
      return null;
    }
  }
}
