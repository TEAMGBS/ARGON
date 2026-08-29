import type { ChatInputCommandInteraction } from 'discord.js';
import { isValidTag, normalizeTag } from '../../util/helper.js';
import type { Client } from './Client.js';

export interface ResolveResult<T> {
  data: T | null;
  error?: string;
}

/**
 * Resolves command arguments into Player/Clan objects. Accepts a raw tag, a saved alias,
 * a Discord @mention (looked up via that user's default linked account), or falls back to the
 * invoking user's own default linked account when no argument is given.
 */
export class Resolver {
  public constructor(private readonly client: Client) {}

  /** Resolve a clan from an explicit arg, an alias, or the guild's first linked clan. */
  public async resolveClan(
    interaction: ChatInputCommandInteraction,
    arg?: string | null
  ): Promise<ResolveResult<Awaited<ReturnType<Client['coc']['getClan']>>>> {
    let tag = arg?.trim();

    if (tag && !isValidTag(tag)) {
      // Treat as an alias within this guild.
      const alias = interaction.guildId
        ? await this.client.db.aliases.findOne({ guildId: interaction.guildId, name: tag.toLowerCase() })
        : null;
      if (alias) tag = alias.tag;
    }

    if (!tag && interaction.guildId) {
      // Fall back to the first clan linked in this guild.
      const store = await this.client.db.clanStores.findOne({ guildId: interaction.guildId });
      if (store) tag = store.tag;
    }

    if (!tag) return { data: null, error: 'No clan tag provided and no clan is linked to this server.' };
    if (!isValidTag(tag)) return { data: null, error: `\`${tag}\` is not a valid clan tag or alias.` };

    const clan = await this.client.coc.getClan(tag);
    if (!clan) return { data: null, error: `No clan found for tag \`${normalizeTag(tag)}\`.` };
    return { data: clan };
  }

  /** Resolve a player from an explicit tag, a @mention, or the invoker's default linked account. */
  public async resolvePlayer(
    interaction: ChatInputCommandInteraction,
    arg?: string | null,
    mentionId?: string | null
  ): Promise<ResolveResult<Awaited<ReturnType<Client['coc']['getPlayer']>>>> {
    let tag = arg?.trim() || null;

    if (!tag) {
      const userId = mentionId || interaction.user.id;
      const link = await this.client.db.playerLinks.findOne({ userId }, { sort: { order: 1 } });
      if (link) tag = link.tag;
    }

    if (!tag) {
      return {
        data: null,
        error: mentionId
          ? 'That user has no linked Clash of Clans account.'
          : 'Provide a player tag, or link your account with `/link`.'
      };
    }
    if (!isValidTag(tag)) return { data: null, error: `\`${tag}\` is not a valid player tag.` };

    const player = await this.client.coc.getPlayer(tag);
    if (!player) return { data: null, error: `No player found for tag \`${normalizeTag(tag)}\`.` };
    return { data: player };
  }

  /** Autocomplete suggestions for clan tags/aliases linked in the current guild. */
  public async clanAutocomplete(guildId: string | null, query: string) {
    if (!guildId) return [];
    const stores = await this.client.db.clanStores.find({ guildId }).limit(25).toArray();
    const q = query.toLowerCase();
    return stores
      .filter((s) => !q || s.name.toLowerCase().includes(q) || s.tag.toLowerCase().includes(q) || s.alias?.includes(q))
      .slice(0, 25)
      .map((s) => ({ name: `${s.name} (${s.tag})`.slice(0, 100), value: s.tag }));
  }
}
