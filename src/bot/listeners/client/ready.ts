import { ActivityType, Events } from 'discord.js';
import { Listener } from '../../struct/Listener.js';

export default class ReadyListener extends Listener {
  public constructor() {
    super('ready', { event: Events.ClientReady, emitter: 'client', once: true });
  }

  public exec() {
    const tag = this.client.user?.tag;
    const guilds = this.client.guilds.cache.size;
    this.client.log.info(`Logged in as ${tag} — serving ${guilds} guild(s).`);
    this.client.user?.setActivity({ name: '/help • Clash of Clans', type: ActivityType.Watching });
  }
}
