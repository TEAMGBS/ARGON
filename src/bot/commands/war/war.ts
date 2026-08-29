import { AutocompleteInteraction, SlashCommandBuilder, type ChatInputCommandInteraction } from 'discord.js';
import { Command } from '../../struct/Command.js';
import { baseEmbed } from '../../../util/embeds.js';
import { EMOJIS } from '../../../util/emojis.js';
import { WAR_STATE } from '../../../util/constants.js';
import { relativeTimestamp } from '../../../util/helper.js';

/** Current war status for a clan. */
export default class WarCommand extends Command {
  public constructor() {
    super('war', { category: 'war', description: 'Show a clan’s current war.', defer: true });
  }

  public builder() {
    return new SlashCommandBuilder()
      .setName('war')
      .setDescription('Show a clan’s current war.')
      .addStringOption((opt) => opt.setName('tag').setDescription('Clan tag or alias.').setAutocomplete(true));
  }

  public async autocomplete(interaction: AutocompleteInteraction, args: Record<string, any>) {
    await interaction.respond(await this.client.resolver.clanAutocomplete(interaction.guildId, String(args.tag ?? '')));
  }

  public async exec(interaction: ChatInputCommandInteraction, args: Record<string, any>) {
    const { data: clan, error } = await this.client.resolver.resolveClan(interaction, args.tag);
    if (!clan) return interaction.editReply(error!);

    const war = await this.client.coc.getCurrentWar(clan.tag);
    if (!war) return interaction.editReply('War log is private or the clan is not currently in a war.');
    if (war.state === 'notInWar') return interaction.editReply(`${clan.name} is not currently in a war.`);

    const w = war as any;
    const embed = baseEmbed(this.client, interaction)
      .setTitle(`${w.clan.name} vs ${w.opponent.name}`)
      .setDescription(
        [
          `**State:** ${WAR_STATE[w.state] ?? w.state}`,
          `**Team Size:** ${w.teamSize}v${w.teamSize}`,
          w.state === 'preparation'
            ? `**Battle day:** ${relativeTimestamp(w.startTime)}`
            : `**Ends:** ${relativeTimestamp(w.endTime)}`
        ].join('\n')
      )
      .addFields(
        {
          name: w.clan.name,
          value: `${EMOJIS.WAR_STAR} ${w.clan.stars}  ${EMOJIS.SWORD} ${w.clan.attackCount}\n💥 ${w.clan.destruction.toFixed(2)}%`,
          inline: true
        },
        {
          name: w.opponent.name,
          value: `${EMOJIS.WAR_STAR} ${w.opponent.stars}  ${EMOJIS.SWORD} ${w.opponent.attackCount}\n💥 ${w.opponent.destruction.toFixed(2)}%`,
          inline: true
        }
      );

    if (w.state === 'warEnded') {
      const result =
        w.clan.stars > w.opponent.stars ||
        (w.clan.stars === w.opponent.stars && w.clan.destruction > w.opponent.destruction)
          ? 'Won 🎉'
          : w.clan.stars === w.opponent.stars && w.clan.destruction === w.opponent.destruction
            ? 'Draw'
            : 'Lost';
      embed.addFields({ name: 'Result', value: result });
    }

    return interaction.editReply({ embeds: [embed] });
  }
}
