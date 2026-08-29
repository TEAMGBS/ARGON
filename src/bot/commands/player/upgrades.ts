import { SlashCommandBuilder, type ChatInputCommandInteraction } from 'discord.js';
import { Command } from '../../struct/Command.js';
import { baseEmbed } from '../../../util/embeds.js';
import { pad, padStart } from '../../../util/helper.js';

/** Lists units that are not yet at their current max level (i.e. available to upgrade). */
export default class UpgradesCommand extends Command {
  public constructor() {
    super('upgrades', { category: 'player', description: 'List a player’s available upgrades.', defer: true });
  }

  public builder() {
    return new SlashCommandBuilder()
      .setName('upgrades')
      .setDescription('List a player’s available upgrades.')
      .addStringOption((opt) => opt.setName('tag').setDescription('Player tag. Defaults to your linked account.'))
      .addUserOption((opt) => opt.setName('user').setDescription('Show another linked user.'));
  }

  private table(items: { name: string; level: number; maxLevel: number }[]): string {
    const pending = items.filter((u) => u.level < u.maxLevel);
    if (!pending.length) return '_all maxed_';
    return pending
      .map((u) => `\`${pad(u.name, 18)} ${padStart(u.level, 2)} → ${padStart(u.maxLevel, 2)}\``)
      .join('\n')
      .slice(0, 1024);
  }

  public async exec(interaction: ChatInputCommandInteraction, args: Record<string, any>) {
    const { data: player, error } = await this.client.resolver.resolvePlayer(interaction, args.tag, args.user);
    if (!player) return interaction.editReply(error!);

    const home = <T extends { village: string }>(arr: T[]) => arr.filter((x) => x.village === 'home');
    const embed = baseEmbed(this.client, interaction)
      .setTitle(`${player.name} (${player.tag}) — Upgrades Available`)
      .addFields(
        { name: 'Heroes', value: this.table(home(player.heroes)) },
        { name: 'Troops', value: this.table(home(player.troops)) },
        { name: 'Spells', value: this.table(home(player.spells)) }
      );

    return interaction.editReply({ embeds: [embed] });
  }
}
