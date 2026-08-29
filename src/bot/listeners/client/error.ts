import { Events } from 'discord.js';
import { Listener } from '../../struct/Listener.js';

export default class ErrorListener extends Listener {
  public constructor() {
    super('error', { event: Events.Error, emitter: 'client' });
  }

  public exec(error: Error) {
    this.client.log.error('Discord client error:', error);
  }
}
