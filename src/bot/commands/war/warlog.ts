import { AutocompleteInteraction, SlashCommandBuilder, type ChatInputCommandInteraction } from 'discord.js';
import { Command } from '../../struct/Command.js';
import { baseEmbed } from '../../../util/embeds.js';
import { EMOJIS } from '../../../util/emojis.js';

/** Historical war results for a clan. */
export default class WarLogCommand extends Command {
  public constructor() {
    super('warlog', { category: 'war', description: 'Show a clan’s recent war results.', defer: true });
  }

  public builder() {
    return new SlashCommandBuilder()
      .setName('warlog')
      .setDescription('Show a clan’s recent war results.')
      .addStringOption((opt) => opt.setName('tag').setDescription('Clan tag or alias.').setAutocomplete(true));
  }

  public async autocomplete(interaction: AutocompleteInteraction, args: Record<string, any>) {
    await interaction.respond(await this.client.resolver.clanAutocomplete(interaction.guildId, String(args.tag ?? '')));
  }

  public async exec(interaction: ChatInputCommandInteraction, args: Record<string, any>) {
    const { data: clan, error } = await this.client.resolver.resolveClan(interaction, args.tag);
    if (!clan) return interaction.editReply(error!);

    const log = await this.client.coc.getWarLog(clan.tag);
    if (!log || !log.length) return interaction.editReply('War log is private or empty.');

    const icon = (result: string | null) =>
      result === 'win' ? EMOJIS.CHECK : result === 'lose' ? EMOJIS.CROSS : '➖';

    const lines = log.slice(0, 15).map((war: any) => {
      const opp = war.opponent?.name ?? 'Unknown (CWL)';
      return `${icon(war.result)} vs **${opp}** — ${EMOJIS.WAR_STAR} ${war.clan.stars}-${war.opponent?.stars ?? 0} • ${war.clan.destructionPercentage?.toFixed(1) ?? '?'}%`;
    });

    const embed = baseEmbed(this.client, interaction)
      .setTitle(`${clan.name} (${clan.tag}) — War Log`)
      .setDescription(lines.join('\n').slice(0, 4000));

    return interaction.editReply({ embeds: [embed] });
  }
}
