import type { Client } from './Client.js';

export interface ListenerOptions {
  /** The event name to bind to. */
  event: string;
  /** Which emitter to bind on. 'client' = the discord.js Client. */
  emitter?: 'client' | 'process';
  /** Bind with `once` instead of `on`. */
  once?: boolean;
}

/** Base class for gateway/process event listeners. Auto-loaded by the ListenerHandler. */
export abstract class Listener {
  public client!: Client;

  public constructor(
    public readonly id: string,
    public readonly options: ListenerOptions
  ) {}

  public abstract exec(...args: any[]): Promise<unknown> | unknown;
}
