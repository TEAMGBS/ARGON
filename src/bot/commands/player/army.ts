import { SlashCommandBuilder, type ChatInputCommandInteraction } from 'discord.js';
import { Command } from '../../struct/Command.js';
import { baseEmbed } from '../../../util/embeds.js';
import { EMOJIS } from '../../../util/emojis.js';

export default class ArmyCommand extends Command {
  public constructor() {
    super('army', {
      category: 'player',
      description: 'Show maxed hero/troop/spell progress for a player.',
      defer: true
    });
  }

  public builder() {
    return new SlashCommandBuilder()
      .setName('army')
      .setDescription('Show maxed hero/troop/spell progress for a player.')
      .addStringOption((opt) => opt.setName('tag').setDescription('Player tag. Defaults to your linked account.'))
      .addUserOption((opt) => opt.setName('user').setDescription('Show another linked user.'));
  }

  private progress(items: { level: number; maxLevel: number }[]): string {
    if (!items.length) return '—';
    const maxed = items.filter((i) => i.level >= i.maxLevel).length;
    const pct = Math.round((maxed / items.length) * 100);
    return `${maxed}/${items.length} maxed (${pct}%)`;
  }

  public async exec(interaction: ChatInputCommandInteraction, args: Record<string, any>) {
    const { data: player, error } = await this.client.resolver.resolvePlayer(interaction, args.tag, args.user);
    if (!player) return interaction.editReply(error!);

    const home = <T extends { village: string }>(arr: T[]) => arr.filter((x) => x.village === 'home');
    const embed = baseEmbed(this.client, interaction)
      .setTitle(`${player.name} (${player.tag}) — Army Progress`)
      .addFields(
        { name: `${EMOJIS.HERO} Heroes`, value: this.progress(home(player.heroes)), inline: true },
        { name: `${EMOJIS.TROOP} Troops`, value: this.progress(home(player.troops)), inline: true },
        { name: `${EMOJIS.SPELL} Spells`, value: this.progress(home(player.spells)), inline: true }
      );

    return interaction.editReply({ embeds: [embed] });
  }
}
