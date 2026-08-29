import { SlashCommandBuilder, type ChatInputCommandInteraction } from 'discord.js';
import { Command } from '../../struct/Command.js';
import { baseEmbed } from '../../../util/embeds.js';
import { pad, padStart } from '../../../util/helper.js';

/**
 * A unit is "rushed" when it's below the max level it could have reached at the *previous*
 * Town Hall — i.e. the player advanced their TH without maxing prior content.
 * We approximate this with the API's per-unit maxLevel scaling: a unit is rushed if its level is
 * meaningfully below the max attainable one TH ago. Without the full offline max-level tables we use
 * a conservative heuristic (below 60% of current max) and clearly label it as an estimate.
 */
export default class RushedCommand extends Command {
  public constructor() {
    super('rushed', { category: 'player', description: 'Estimate a player’s rushed units.', defer: true });
  }

  public builder() {
    return new SlashCommandBuilder()
      .setName('rushed')
      .setDescription('Estimate a player’s rushed units.')
      .addStringOption((opt) => opt.setName('tag').setDescription('Player tag. Defaults to your linked account.'))
      .addUserOption((opt) => opt.setName('user').setDescription('Show another linked user.'));
  }

  public async exec(interaction: ChatInputCommandInteraction, args: Record<string, any>) {
    const { data: player, error } = await this.client.resolver.resolvePlayer(interaction, args.tag, args.user);
    if (!player) return interaction.editReply(error!);

    const home = <T extends { village: string }>(arr: T[]) => arr.filter((x) => x.village === 'home');
    const all = [...home(player.heroes), ...home(player.troops), ...home(player.spells)];
    const rushed = all.filter((u) => u.level > 0 && u.level < Math.floor(u.maxLevel * 0.6));

    const embed = baseEmbed(this.client, interaction).setTitle(`${player.name} (${player.tag}) — Rushed (estimate)`);
    if (!rushed.length) {
      embed.setDescription('No significantly under-leveled units detected. 👍');
    } else {
      embed.setDescription(
        rushed
          .map((u) => `\`${pad(u.name, 18)} ${padStart(u.level, 2)}/${padStart(u.maxLevel, 2)}\``)
          .join('\n')
          .slice(0, 4000)
      );
      embed.setFooter({ text: 'Heuristic estimate — units below 60% of current max level.' });
    }

    return interaction.editReply({ embeds: [embed] });
  }
}
