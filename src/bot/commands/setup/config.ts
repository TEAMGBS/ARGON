import {
  MessageFlags,
  PermissionFlagsBits,
  SlashCommandBuilder,
  type ChatInputCommandInteraction
} from 'discord.js';
import moment from 'moment-timezone';
import { Command } from '../../struct/Command.js';
import { baseEmbed } from '../../../util/embeds.js';
import { EMOJIS } from '../../../util/emojis.js';

/** Per-server settings: embed color and timezone. */
export default class ConfigCommand extends Command {
  public constructor() {
    super('config', {
      category: 'setup',
      description: 'View or change server settings.',
      guildOnly: true,
      userPermissions: [PermissionFlagsBits.ManageGuild]
    });
  }

  public builder() {
    return new SlashCommandBuilder()
      .setName('config')
      .setDescription('View or change server settings.')
      .setDefaultMemberPermissions(PermissionFlagsBits.ManageGuild)
      .addStringOption((opt) => opt.setName('color').setDescription('Embed color hex, e.g. 5865F2.'))
      .addStringOption((opt) => opt.setName('timezone').setDescription('Server timezone id, e.g. Europe/London.'));
  }

  public async exec(interaction: ChatInputCommandInteraction, args: Record<string, any>) {
    const patch: Record<string, string> = {};

    if (args.color) {
      const hex = String(args.color).replace(/^#/, '');
      if (!/^[0-9a-fA-F]{6}$/.test(hex)) {
        return interaction.reply({ content: 'Color must be a 6-digit hex, e.g. `5865F2`.', flags: MessageFlags.Ephemeral });
      }
      patch.color = hex;
    }
    if (args.timezone) {
      if (!moment.tz.zone(String(args.timezone))) {
        return interaction.reply({ content: 'Invalid timezone id.', flags: MessageFlags.Ephemeral });
      }
      patch.timezone = String(args.timezone);
    }

    if (Object.keys(patch).length) {
      await this.client.settings.set(interaction.guildId!, patch);
    }

    const settings = this.client.settings.get(interaction.guildId!);
    const embed = baseEmbed(this.client, interaction)
      .setTitle('Server Settings')
      .setDescription(Object.keys(patch).length ? `${EMOJIS.CHECK} Updated.` : 'Current configuration:')
      .addFields(
        { name: 'Embed color', value: `#${settings?.color ?? process.env.EMBED_COLOR ?? '5865F2'}`, inline: true },
        { name: 'Timezone', value: settings?.timezone ?? 'UTC', inline: true }
      );

    return interaction.reply({ embeds: [embed] });
  }
}
