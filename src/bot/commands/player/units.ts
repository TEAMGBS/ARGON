import { SlashCommandBuilder, type ChatInputCommandInteraction } from 'discord.js';
import { Command } from '../../struct/Command.js';
import { baseEmbed } from '../../../util/embeds.js';
import { EMOJIS } from '../../../util/emojis.js';
import { pad, padStart } from '../../../util/helper.js';

export default class UnitsCommand extends Command {
  public constructor() {
    super('units', { category: 'player', description: "Show a player's troop, spell and hero levels.", defer: true });
  }

  public builder() {
    return new SlashCommandBuilder()
      .setName('units')
      .setDescription("Show a player's troop, spell and hero levels.")
      .addStringOption((opt) => opt.setName('tag').setDescription('Player tag. Defaults to your linked account.'))
      .addUserOption((opt) => opt.setName('user').setDescription('Show another linked user.'));
  }

  private table(items: { name: string; level: number; maxLevel: number }[]): string {
    if (!items.length) return '_none_';
    return items
      .map((u) => `\`${pad(u.name, 18)} ${padStart(u.level, 2)}/${padStart(u.maxLevel, 2)}\``)
      .join('\n')
      .slice(0, 1024);
  }

  public async exec(interaction: ChatInputCommandInteraction, args: Record<string, any>) {
    const { data: player, error } = await this.client.resolver.resolvePlayer(interaction, args.tag, args.user);
    if (!player) return interaction.editReply(error!);

    const home = <T extends { village: string }>(arr: T[]) => arr.filter((x) => x.village === 'home');
    const pets = ((player as any).pets ?? []) as { name: string; level: number; maxLevel: number }[];

    const embed = baseEmbed(this.client, interaction).setTitle(`${player.name} (${player.tag}) — Units`);
    embed.addFields({ name: `${EMOJIS.HERO} Heroes`, value: this.table(home(player.heroes)) });
    if (pets.length) embed.addFields({ name: `${EMOJIS.PET} Pets`, value: this.table(pets) });
    embed.addFields(
      { name: `${EMOJIS.TROOP} Troops`, value: this.table(home(player.troops)) },
      { name: `${EMOJIS.SPELL} Spells`, value: this.table(home(player.spells)) }
    );

    return interaction.editReply({ embeds: [embed] });
  }
}
