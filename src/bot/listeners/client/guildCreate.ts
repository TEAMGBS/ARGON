import { Events, type Guild } from 'discord.js';
import { Listener } from '../../struct/Listener.js';

export default class GuildCreateListener extends Listener {
  public constructor() {
    super('guildCreate', { event: Events.GuildCreate, emitter: 'client' });
  }

  public async exec(guild: Guild) {
    this.client.log.info(`Joined guild ${guild.name} (${guild.id}) — ${guild.memberCount} members.`);
    // Ensure a settings document exists so caches and color lookups work immediately.
    if (!this.client.settings.get(guild.id)) {
      await this.client.settings.set(guild.id, {});
    }
  }
}
