import { AutocompleteInteraction, SlashCommandBuilder, type ChatInputCommandInteraction } from 'discord.js';
import { Command } from '../../struct/Command.js';
import { baseEmbed } from '../../../util/embeds.js';
import { EMOJIS } from '../../../util/emojis.js';
import { padStart } from '../../../util/helper.js';

/** Town Hall composition of a clan's members. */
export default class CompoCommand extends Command {
  public constructor() {
    super('compo', { category: 'clan', description: 'Show a clan’s Town Hall composition.', defer: true });
  }

  public builder() {
    return new SlashCommandBuilder()
      .setName('compo')
      .setDescription('Show a clan’s Town Hall composition.')
      .addStringOption((opt) =>
        opt.setName('tag').setDescription('Clan tag or alias.').setAutocomplete(true)
      );
  }

  public async autocomplete(interaction: AutocompleteInteraction, args: Record<string, any>) {
    await interaction.respond(await this.client.resolver.clanAutocomplete(interaction.guildId, String(args.tag ?? '')));
  }

  public async exec(interaction: ChatInputCommandInteraction, args: Record<string, any>) {
    const { data: clan, error } = await this.client.resolver.resolveClan(interaction, args.tag);
    if (!clan) return interaction.editReply(error!);

    // Member list from the clan endpoint doesn't include TH level, so fetch each member's profile
    // in parallel (bounded by the clan size of 50).
    const players = await Promise.all(clan.members.map((m) => this.client.coc.getPlayer(m.tag)));
    const counts = new Map<number, number>();
    let total = 0;
    for (const p of players) {
      if (!p) continue;
      counts.set(p.townHallLevel, (counts.get(p.townHallLevel) ?? 0) + 1);
      total++;
    }

    const rows = [...counts.entries()]
      .sort((a, b) => b[0] - a[0])
      .map(([th, n]) => `${EMOJIS.TOWN_HALL} \`TH${padStart(th, 2)}\` — **${n}**`);

    const embed = baseEmbed(this.client, interaction)
      .setTitle(`${clan.name} (${clan.tag}) — Composition`)
      .setDescription(rows.join('\n') || '_No data._')
      .setFooter({ text: `${total} members` });

    return interaction.editReply({ embeds: [embed] });
  }
}
