import { SlashCommandBuilder, type ChatInputCommandInteraction } from 'discord.js';
import { Command } from '../../struct/Command.js';

export default class PingCommand extends Command {
  public constructor() {
    super('ping', { category: 'util', description: 'Check the bot latency.' });
  }

  public builder() {
    return new SlashCommandBuilder().setName('ping').setDescription('Check the bot latency.');
  }

  public async exec(interaction: ChatInputCommandInteraction) {
    const sent = await interaction.reply({ content: 'Pinging…', fetchReply: true });
    const rtt = sent.createdTimestamp - interaction.createdTimestamp;
    await interaction.editReply(`🏓 Pong! Round-trip \`${rtt}ms\` • Gateway \`${Math.round(this.client.ws.ping)}ms\``);
  }
}
