import { SlashCommandBuilder, version as djsVersion, type ChatInputCommandInteraction } from 'discord.js';
import { Command } from '../../struct/Command.js';
import { baseEmbed } from '../../../util/embeds.js';
import { duration } from '../../../util/helper.js';

export default class StatusCommand extends Command {
  public constructor() {
    super('status', { category: 'util', description: 'Show bot status and uptime.' });
  }

  public builder() {
    return new SlashCommandBuilder().setName('status').setDescription('Show bot status and uptime.');
  }

  public async exec(interaction: ChatInputCommandInteraction) {
    const mem = process.memoryUsage().heapUsed / 1024 / 1024;
    const embed = baseEmbed(this.client, interaction)
      .setTitle('ARGON — Status')
      .addFields(
        { name: 'Uptime', value: duration(this.client.uptime ?? 0), inline: true },
        { name: 'Guilds', value: `${this.client.guilds.cache.size}`, inline: true },
        { name: 'Gateway', value: `${Math.round(this.client.ws.ping)}ms`, inline: true },
        { name: 'Memory', value: `${mem.toFixed(1)} MB`, inline: true },
        { name: 'discord.js', value: `v${djsVersion}`, inline: true },
        { name: 'Node', value: process.version, inline: true }
      );
    await interaction.reply({ embeds: [embed] });
  }
}
