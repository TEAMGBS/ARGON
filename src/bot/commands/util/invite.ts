import { PermissionFlagsBits, SlashCommandBuilder, type ChatInputCommandInteraction } from 'discord.js';
import { Command } from '../../struct/Command.js';
import { baseEmbed } from '../../../util/embeds.js';

export default class InviteCommand extends Command {
  public constructor() {
    super('invite', { category: 'util', description: 'Get the bot invite and support links.' });
  }

  public builder() {
    return new SlashCommandBuilder().setName('invite').setDescription('Get the bot invite and support links.');
  }

  public async exec(interaction: ChatInputCommandInteraction) {
    const clientId = process.env.CLIENT_ID ?? this.client.user?.id ?? '';
    const perms =
      PermissionFlagsBits.ViewChannel |
      PermissionFlagsBits.SendMessages |
      PermissionFlagsBits.EmbedLinks |
      PermissionFlagsBits.ManageRoles |
      PermissionFlagsBits.ManageWebhooks;
    const invite = `https://discord.com/oauth2/authorize?client_id=${clientId}&permissions=${perms}&scope=bot%20applications.commands`;
    const support = process.env.SUPPORT_SERVER || 'https://discord.gg/';

    const embed = baseEmbed(this.client, interaction)
      .setTitle('Invite ARGON')
      .setDescription([`• [Add me to your server](${invite})`, `• [Support server](${support})`].join('\n'));
    await interaction.reply({ embeds: [embed] });
  }
}
