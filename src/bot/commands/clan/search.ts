import { SlashCommandBuilder, type ChatInputCommandInteraction } from 'discord.js';
import { Command } from '../../struct/Command.js';
import { baseEmbed } from '../../../util/embeds.js';
import { EMOJIS } from '../../../util/emojis.js';

/** Search public clans by name. */
export default class SearchCommand extends Command {
  public constructor() {
    super('search', { category: 'clan', description: 'Search clans by name.', defer: true });
  }

  public builder() {
    return new SlashCommandBuilder()
      .setName('search')
      .setDescription('Search clans by name.')
      .addStringOption((opt) => opt.setName('name').setDescription('Clan name to search for.').setRequired(true));
  }

  public async exec(interaction: ChatInputCommandInteraction, args: Record<string, any>) {
    const result = await this.client.coc.searchClans(String(args.name), 10);
    if (!result || !result.length) return interaction.editReply('No clans found for that name.');

    const lines = result.map(
      (c) =>
        `${EMOJIS.CLAN} **${c.name}** (${c.tag}) — Lv ${c.level} • ${EMOJIS.PEOPLE} ${c.memberCount}/50 • ${EMOJIS.TROPHY} ${c.points}`
    );

    const embed = baseEmbed(this.client, interaction)
      .setTitle(`Clan search — "${args.name}"`)
      .setDescription(lines.join('\n').slice(0, 4000));

    return interaction.editReply({ embeds: [embed] });
  }
}
