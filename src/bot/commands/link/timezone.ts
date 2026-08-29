import { MessageFlags, SlashCommandBuilder, type ChatInputCommandInteraction } from 'discord.js';
import moment from 'moment-timezone';
import { Command } from '../../struct/Command.js';
import { EMOJIS } from '../../../util/emojis.js';

/** Store a user's IANA timezone for rendering times in their local zone. */
export default class TimezoneCommand extends Command {
  public constructor() {
    super('timezone', { category: 'link', description: 'Set your timezone.' });
  }

  public builder() {
    return new SlashCommandBuilder()
      .setName('timezone')
      .setDescription('Set your timezone (e.g. Europe/London).')
      .addStringOption((opt) =>
        opt.setName('zone').setDescription('IANA timezone id, e.g. America/New_York.').setRequired(true).setAutocomplete(true)
      );
  }

  public async autocomplete(interaction: import('discord.js').AutocompleteInteraction, args: Record<string, any>) {
    const q = String(args.zone ?? '').toLowerCase();
    const zones = moment.tz
      .names()
      .filter((z) => z.toLowerCase().includes(q))
      .slice(0, 25)
      .map((z) => ({ name: z, value: z }));
    await interaction.respond(zones);
  }

  public async exec(interaction: ChatInputCommandInteraction, args: Record<string, any>) {
    const zone = String(args.zone);
    if (!moment.tz.zone(zone)) {
      return interaction.reply({ content: `\`${zone}\` is not a valid timezone id.`, flags: MessageFlags.Ephemeral });
    }
    await this.client.db.users.updateOne(
      { userId: interaction.user.id },
      { $set: { userId: interaction.user.id, timezone: zone, updatedAt: new Date() } },
      { upsert: true }
    );
    const now = moment().tz(zone).format('HH:mm');
    return interaction.reply({ content: `${EMOJIS.CHECK} Timezone set to \`${zone}\` (local time ${now}).`, flags: MessageFlags.Ephemeral });
  }
}
