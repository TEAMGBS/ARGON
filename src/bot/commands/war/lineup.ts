import { AutocompleteInteraction, SlashCommandBuilder, type ChatInputCommandInteraction } from 'discord.js';
import { Command } from '../../struct/Command.js';
import { baseEmbed } from '../../../util/embeds.js';
import { pad, padStart } from '../../../util/helper.js';

/** War lineup — both sides ordered by map position with Town Hall levels. */
export default class LineupCommand extends Command {
  public constructor() {
    super('lineup', { category: 'war', description: 'Show the war lineup for both sides.', defer: true });
  }

  public builder() {
    return new SlashCommandBuilder()
      .setName('lineup')
      .setDescription('Show the war lineup for both sides.')
      .addStringOption((opt) => opt.setName('tag').setDescription('Clan tag or alias.').setAutocomplete(true));
  }

  public async autocomplete(interaction: AutocompleteInteraction, args: Record<string, any>) {
    await interaction.respond(await this.client.resolver.clanAutocomplete(interaction.guildId, String(args.tag ?? '')));
  }

  private side(members: any[]): string {
    return members
      .sort((a, b) => a.mapPosition - b.mapPosition)
      .map((m, i) => `\`${padStart(i + 1, 2)} TH${padStart(m.townHallLevel, 2)} ${pad(m.name, 15)}\``)
      .join('\n')
      .slice(0, 1024);
  }

  public async exec(interaction: ChatInputCommandInteraction, args: Record<string, any>) {
    const { data: clan, error } = await this.client.resolver.resolveClan(interaction, args.tag);
    if (!clan) return interaction.editReply(error!);

    const war = await this.client.coc.getCurrentWar(clan.tag);
    if (!war || war.state === 'notInWar') return interaction.editReply('Clan is not currently in a war.');
    const w = war as any;

    const embed = baseEmbed(this.client, interaction)
      .setTitle(`${w.clan.name} vs ${w.opponent.name} — Lineup`)
      .addFields(
        { name: w.clan.name, value: this.side(w.clan.members), inline: true },
        { name: w.opponent.name, value: this.side(w.opponent.members), inline: true }
      );

    return interaction.editReply({ embeds: [embed] });
  }
}
