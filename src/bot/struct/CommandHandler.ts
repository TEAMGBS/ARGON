import { readdirp } from 'readdirp';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { dirname, resolve } from 'node:path';
import {
  Collection,
  Events,
  InteractionType,
  MessageFlags,
  type Interaction,
  type ChatInputCommandInteraction
} from 'discord.js';
import { Command } from './Command.js';
import { Logger } from '../../util/logger.js';
import type { Client } from './Client.js';

/**
 * Discovers command classes under src/bot/commands, builds the slash-command JSON, and dispatches
 * interactions (chat-input, autocomplete, buttons, select menus). Adding a command file is all
 * that's needed to register a new command — this is the single extension point.
 */
export class CommandHandler {
  public modules = new Collection<string, Command>();
  private readonly log = new Logger('CommandHandler');

  public constructor(private readonly client: Client) {}

  public async loadAll(): Promise<void> {
    const here = dirname(fileURLToPath(import.meta.url));
    const dir = resolve(here, '../commands');
    const isModule = (name: string) => /\.(js|ts)$/.test(name) && !name.endsWith('.d.ts');
    for await (const entry of readdirp(dir, { fileFilter: (e) => isModule(e.basename), depth: 5, type: 'files' })) {
      const mod = await import(pathToFileURL(entry.fullPath).href);
      const Ctor = mod.default;
      if (typeof Ctor !== 'function') continue;
      const command: Command = new Ctor();
      if (!(command instanceof Command)) continue;
      command.client = this.client;
      this.modules.set(command.id, command);
    }
    this.log.info(`Loaded ${this.modules.size} commands.`);
  }

  /** JSON payloads for registering commands with Discord. */
  public toJSON() {
    return [...this.modules.values()].map((cmd) => cmd.builder().toJSON());
  }

  public register(): void {
    this.client.on(Events.InteractionCreate, (interaction) => this.onInteraction(interaction));
  }

  private async onInteraction(interaction: Interaction): Promise<void> {
    try {
      if (interaction.type === InteractionType.ApplicationCommandAutocomplete) {
        const command = this.modules.get(interaction.commandName);
        if (command?.autocomplete) {
          await command.autocomplete(interaction, this.args(interaction));
        }
        return;
      }

      if (interaction.isChatInputCommand()) {
        await this.execCommand(interaction);
        return;
      }

      // Route component interactions by customId convention: "<commandId>:<...args>"
      if (interaction.isButton() || interaction.isStringSelectMenu()) {
        const [commandId, ...args] = interaction.customId.split(':');
        const command = this.modules.get(commandId);
        if (!command) return;
        if (interaction.isButton() && command.handleButton) await command.handleButton(interaction, args);
        if (interaction.isStringSelectMenu() && command.handleSelect) await command.handleSelect(interaction, args);
      }
    } catch (error) {
      this.log.error('Interaction handling failed:', error);
    }
  }

  private async execCommand(interaction: ChatInputCommandInteraction): Promise<void> {
    const command = this.modules.get(interaction.commandName);
    if (!command) return;

    if (command.options.guildOnly && !interaction.inGuild()) {
      await interaction.reply({ content: 'This command can only be used in a server.', flags: MessageFlags.Ephemeral });
      return;
    }

    if (command.options.userPermissions?.length && interaction.inGuild()) {
      const missing = command.options.userPermissions.filter((perm) => !interaction.memberPermissions?.has(perm));
      if (missing.length) {
        await interaction.reply({
          content: 'You do not have permission to use this command.',
          flags: MessageFlags.Ephemeral
        });
        return;
      }
    }

    if (command.options.defer) {
      await interaction.deferReply(command.options.ephemeral ? { flags: MessageFlags.Ephemeral } : {});
    }

    try {
      await command.exec(interaction, this.args(interaction));
    } catch (error) {
      this.log.error(`Command '${command.id}' failed:`, error);
      const payload = { content: 'Something went wrong while running that command.' };
      if (interaction.deferred || interaction.replied) await interaction.editReply(payload).catch(() => null);
      else await interaction.reply({ ...payload, flags: MessageFlags.Ephemeral }).catch(() => null);
    }
  }

  /** Flatten interaction options (including subcommand) into a plain args object. */
  private args(interaction: ChatInputCommandInteraction | Interaction): Record<string, any> {
    const out: Record<string, any> = {};
    if (!('options' in interaction)) return out;
    const opts: any = interaction.options;
    try {
      const sub = opts.getSubcommand(false);
      if (sub) out.subcommand = sub;
    } catch {
      /* no subcommand */
    }
    try {
      const group = opts.getSubcommandGroup(false);
      if (group) out.subcommandGroup = group;
    } catch {
      /* no group */
    }
    for (const option of opts.data ?? []) this.collectOption(option, out);
    return out;
  }

  private collectOption(option: any, out: Record<string, any>): void {
    if (option.options?.length) {
      for (const child of option.options) this.collectOption(child, out);
    }
    if (option.value !== undefined && option.type !== 1 && option.type !== 2) {
      out[option.name] = option.value;
    }
  }
}
