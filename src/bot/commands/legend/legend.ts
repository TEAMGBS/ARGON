import { SlashCommandBuilder, type ChatInputCommandInteraction } from 'discord.js';
import { Command } from '../../struct/Command.js';
import { baseEmbed } from '../../../util/embeds.js';
import { EMOJIS } from '../../../util/emojis.js';

/**
 * Legend League snapshot for a player. The public CoC API exposes the current legend-season
 * running total and best rank; full per-attack day tracking requires storing snapshots over time
 * (roadmap item). This command shows what the live API provides.
 */
export default class LegendCommand extends Command {
  public constructor() {
    super('legend', { category: 'legend', description: 'Show a player’s Legend League stats.', defer: true });
  }

  public builder() {
    return new SlashCommandBuilder()
      .setName('legend')
      .setDescription('Show a player’s Legend League stats.')
      .addStringOption((opt) => opt.setName('tag').setDescription('Player tag. Defaults to your linked account.'))
      .addUserOption((opt) => opt.setName('user').setDescription('Show another linked user.'));
  }

  public async exec(interaction: ChatInputCommandInteraction, args: Record<string, any>) {
    const { data: player, error } = await this.client.resolver.resolvePlayer(interaction, args.tag, args.user);
    if (!player) return interaction.editReply(error!);

    const legend = (player as any).legendStatistics;
    const embed = baseEmbed(this.client, interaction).setTitle(`${player.name} (${player.tag}) — Legend League`);

    if (player.leagueTier?.name !== 'Legend League' && !legend) {
      embed.setDescription(`This player is currently in **${player.leagueTier?.name ?? 'Unranked'}**, not Legend League.`);
      embed.addFields({ name: 'Trophies', value: `${EMOJIS.TROPHY} ${player.trophies}`, inline: true });
      return interaction.editReply({ embeds: [embed] });
    }

    embed.addFields(
      { name: 'Current Trophies', value: `${EMOJIS.TROPHY} ${player.trophies}`, inline: true },
      { name: 'Best Season', value: `${EMOJIS.TROPHY} ${legend?.bestSeason?.trophies ?? '—'}`, inline: true },
      { name: 'Best Rank', value: `#${legend?.bestSeason?.rank ?? '—'}`, inline: true }
    );
    if (legend?.currentSeason) {
      embed.addFields({
        name: 'Current Season',
        value: `Trophies: ${legend.currentSeason.trophies}`,
        inline: true
      });
    }

    embed.setFooter({ text: 'Per-day attack tracking is a roadmap feature (needs stored snapshots).' });
    return interaction.editReply({ embeds: [embed] });
  }
}
