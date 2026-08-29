import { readdirp } from 'readdirp';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { dirname, resolve } from 'node:path';
import { Collection } from 'discord.js';
import { Listener } from './Listener.js';
import { Logger } from '../../util/logger.js';
import type { Client } from './Client.js';

/** Discovers Listener classes under src/bot/listeners and binds them to their emitters. */
export class ListenerHandler {
  public modules = new Collection<string, Listener>();
  private readonly log = new Logger('ListenerHandler');

  public constructor(private readonly client: Client) {}

  public async loadAll(): Promise<void> {
    const here = dirname(fileURLToPath(import.meta.url));
    const dir = resolve(here, '../listeners');
    const isModule = (name: string) => /\.(js|ts)$/.test(name) && !name.endsWith('.d.ts');
    for await (const entry of readdirp(dir, { fileFilter: (e) => isModule(e.basename), depth: 5, type: 'files' })) {
      const mod = await import(pathToFileURL(entry.fullPath).href);
      const Ctor = mod.default;
      if (typeof Ctor !== 'function') continue;
      const listener: Listener = new Ctor();
      if (!(listener instanceof Listener)) continue;
      listener.client = this.client;
      this.modules.set(listener.id, listener);
      this.bind(listener);
    }
    this.log.info(`Loaded ${this.modules.size} listeners.`);
  }

  private bind(listener: Listener): void {
    const emitter = (
      listener.options.emitter === 'process' ? process : this.client
    ) as unknown as NodeJS.EventEmitter;
    const fn = (...args: any[]) => listener.exec(...args);
    if (listener.options.once) emitter.once(listener.options.event, fn);
    else emitter.on(listener.options.event, fn);
  }
}
