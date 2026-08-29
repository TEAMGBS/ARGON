import type {
  AutocompleteInteraction,
  ButtonInteraction,
  ChatInputCommandInteraction,
  SlashCommandBuilder,
  SlashCommandOptionsOnlyBuilder,
  SlashCommandSubcommandsOnlyBuilder,
  StringSelectMenuInteraction
} from 'discord.js';
import type { Client } from './Client.js';

export interface CommandOptions {
  category: string;
  description: string;
  /** Defer the reply before running exec (for commands that hit the API). */
  defer?: boolean;
  /** Make the (deferred) reply ephemeral. */
  ephemeral?: boolean;
  /** Require the invoking member to have one of these permission flag names. */
  userPermissions?: bigint[];
  /** Only usable inside a guild. */
  guildOnly?: boolean;
}

type AnyBuilder =
  | SlashCommandBuilder
  | SlashCommandOptionsOnlyBuilder
  | SlashCommandSubcommandsOnlyBuilder
  | Omit<SlashCommandBuilder, 'addSubcommand' | 'addSubcommandGroup'>;

/**
 * Base class every command extends. The command handler discovers subclasses, calls `builder()`
 * to assemble the slash-command JSON, and routes interactions to `exec` / `autocomplete` /
 * component handlers.
 */
export abstract class Command {
  public client!: Client;

  public constructor(
    public readonly id: string,
    public readonly options: CommandOptions
  ) {}

  /** Return the discord.js slash-command builder for this command. */
  public abstract builder(): AnyBuilder;

  /** Handle a chat-input (slash) invocation. */
  public abstract exec(interaction: ChatInputCommandInteraction, args: Record<string, any>): Promise<unknown> | unknown;

  /** Optional: provide autocomplete suggestions. */
  public autocomplete?(interaction: AutocompleteInteraction, args: Record<string, any>): Promise<unknown> | unknown;

  /** Optional: handle a button press whose customId is routed to this command. */
  public handleButton?(interaction: ButtonInteraction, args: string[]): Promise<unknown> | unknown;

  /** Optional: handle a select-menu whose customId is routed to this command. */
  public handleSelect?(interaction: StringSelectMenuInteraction, args: string[]): Promise<unknown> | unknown;
}
