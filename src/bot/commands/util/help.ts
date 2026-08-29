import { SlashCommandBuilder, type ChatInputCommandInteraction } from 'discord.js';
import { Command } from '../../struct/Command.js';
import { baseEmbed } from '../../../util/embeds.js';

const CATEGORY_LABELS: Record<string, string> = {
  player: 'Player',
  clan: 'Clan',
  war: 'War',
  cwl: 'Clan War League',
  legend: 'Legend League',
  link: 'Links & Profiles',
  setup: 'Setup & Config',
  reminder: 'Reminders',
  flag: 'Flags',
  export: 'Exports',
  util: 'Utility'
};

export default class HelpCommand extends Command {
  public constructor() {
    super('help', { category: 'util', description: 'List available commands.' });
  }

  public builder() {
    return new SlashCommandBuilder()
      .setName('help')
      .setDescription('List available commands.')
      .addStringOption((opt) => opt.setName('command').setDescription('Show help for a specific command.'));
  }

  public async exec(interaction: ChatInputCommandInteraction, args: Record<string, any>) {
    const modules = this.client.commandHandler.modules;

    if (args.command) {
      const cmd = modules.get(String(args.command).toLowerCase());
      if (!cmd) {
        await interaction.reply({ content: `No command named \`${args.command}\`.`, ephemeral: true });
        return;
      }
      const embed = baseEmbed(this.client, interaction)
        .setTitle(`/${cmd.id}`)
        .setDescription(cmd.options.description)
        .addFields({ name: 'Category', value: CATEGORY_LABELS[cmd.options.category] ?? cmd.options.category });
      await interaction.reply({ embeds: [embed] });
      return;
    }

    const grouped = new Map<string, string[]>();
    for (const cmd of modules.values()) {
      const list = grouped.get(cmd.options.category) ?? [];
      list.push(`\`/${cmd.id}\``);
      grouped.set(cmd.options.category, list);
    }

    const embed = baseEmbed(this.client, interaction)
      .setTitle('ARGON — Commands')
      .setDescription('A ClashPerk-style Clash of Clans bot. Use `/help command:<name>` for details.');

    for (const [category, cmds] of grouped) {
      embed.addFields({ name: CATEGORY_LABELS[category] ?? category, value: cmds.sort().join(' ') });
    }

    await interaction.reply({ embeds: [embed] });
  }
}
