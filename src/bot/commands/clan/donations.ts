import { AutocompleteInteraction, SlashCommandBuilder, type ChatInputCommandInteraction } from 'discord.js';
import { Command } from '../../struct/Command.js';
import { baseEmbed } from '../../../util/embeds.js';
import { EMOJIS } from '../../../util/emojis.js';
import { pad, padStart } from '../../../util/helper.js';

/** Current-season donation leaderboard for a clan. */
export default class DonationsCommand extends Command {
  public constructor() {
    super('donations', { category: 'clan', description: 'Show a clan’s donation leaderboard.', defer: true });
  }

  public builder() {
    return new SlashCommandBuilder()
      .setName('donations')
      .setDescription('Show a clan’s donation leaderboard.')
      .addStringOption((opt) => opt.setName('tag').setDescription('Clan tag or alias.').setAutocomplete(true));
  }

  public async autocomplete(interaction: AutocompleteInteraction, args: Record<string, any>) {
    await interaction.respond(await this.client.resolver.clanAutocomplete(interaction.guildId, String(args.tag ?? '')));
  }

  public async exec(interaction: ChatInputCommandInteraction, args: Record<string, any>) {
    const { data: clan, error } = await this.client.resolver.resolveClan(interaction, args.tag);
    if (!clan) return interaction.editReply(error!);

    const members = [...clan.members].sort((a, b) => b.donations - a.donations);
    let totalDon = 0;
    let totalRec = 0;
    const lines = members.map((m, i) => {
      totalDon += m.donations;
      totalRec += m.received;
      return `\`${padStart(i + 1, 2)} ${pad(m.name, 15)} ${padStart(m.donations, 5)} ${padStart(m.received, 5)}\``;
    });

    const header = `\`${pad('#', 2)} ${pad('Name', 15)} ${pad('Don', 5)} ${pad('Rec', 5)}\``;
    const embed = baseEmbed(this.client, interaction)
      .setTitle(`${clan.name} (${clan.tag}) — Donations`)
      .setDescription([header, ...lines].join('\n').slice(0, 4000))
      .setFooter({ text: `${EMOJIS.DONATE} ${totalDon}  •  ${EMOJIS.RECEIVE} ${totalRec}` });

    return interaction.editReply({ embeds: [embed] });
  }
}
