import { AutocompleteInteraction, SlashCommandBuilder, type ChatInputCommandInteraction } from 'discord.js';
import { Command } from '../../struct/Command.js';
import { baseEmbed } from '../../../util/embeds.js';
import { EMOJIS } from '../../../util/emojis.js';
import { pad, padStart } from '../../../util/helper.js';

/** Clan War League info: the season roster of clans, or the current round's matchup. */
export default class CwlCommand extends Command {
  public constructor() {
    super('cwl', { category: 'cwl', description: 'Show Clan War League roster and rounds.', defer: true });
  }

  public builder() {
    return new SlashCommandBuilder()
      .setName('cwl')
      .setDescription('Show Clan War League roster and rounds.')
      .addSubcommand((sub) =>
        sub
          .setName('roster')
          .setDescription('Show the CWL season roster of clans.')
          .addStringOption((opt) => opt.setName('tag').setDescription('Clan tag or alias.').setAutocomplete(true))
      )
      .addSubcommand((sub) =>
        sub
          .setName('round')
          .setDescription('Show the current CWL round for a clan.')
          .addStringOption((opt) => opt.setName('tag').setDescription('Clan tag or alias.').setAutocomplete(true))
      );
  }

  public async autocomplete(interaction: AutocompleteInteraction, args: Record<string, any>) {
    await interaction.respond(await this.client.resolver.clanAutocomplete(interaction.guildId, String(args.tag ?? '')));
  }

  public async exec(interaction: ChatInputCommandInteraction, args: Record<string, any>) {
    const { data: clan, error } = await this.client.resolver.resolveClan(interaction, args.tag);
    if (!clan) return interaction.editReply(error!);

    const group = await this.client.coc.getCwlGroup(clan.tag);
    if (!group) return interaction.editReply('This clan is not in a Clan War League season right now.');
    const g = group as any;

    if (args.subcommand === 'round') return this.round(interaction, clan, g);
    return this.roster(interaction, clan, g);
  }

  private async roster(interaction: ChatInputCommandInteraction, clan: any, g: any) {
    const lines = g.clans
      .sort((a: any, b: any) => b.clanLevel - a.clanLevel)
      .map((c: any, i: number) => `\`${padStart(i + 1, 2)}\` ${EMOJIS.CLAN} **${c.name}** (${c.tag}) — Lv ${c.clanLevel}`);
    const embed = baseEmbed(this.client, interaction)
      .setTitle(`${clan.name} — CWL Season (${g.season})`)
      .setDescription(lines.join('\n').slice(0, 4000))
      .setFooter({ text: `${g.clans.length} clans • ${g.rounds.length} rounds` });
    return interaction.editReply({ embeds: [embed] });
  }

  private async round(interaction: ChatInputCommandInteraction, clan: any, g: any) {
    // Find the latest round that has a war tag involving this clan.
    const warTags = g.rounds.flatMap((r: any) => r.warTags).filter((t: string) => t && t !== '#0');
    for (const warTag of warTags.reverse()) {
      const war = await this.client.coc.client.getClanWarLeagueRound(warTag).catch(() => null);
      if (!war) continue;
      const w = war as any;
      if (w.clan.tag !== clan.tag && w.opponent.tag !== clan.tag) continue;
      const us = w.clan.tag === clan.tag ? w.clan : w.opponent;
      const them = w.clan.tag === clan.tag ? w.opponent : w.clan;
      const embed = baseEmbed(this.client, interaction)
        .setTitle(`${us.name} vs ${them.name} — CWL Round`)
        .setDescription(
          [
            `**State:** ${w.state}`,
            `${EMOJIS.WAR_STAR} ${us.stars} - ${them.stars}`,
            `💥 ${us.destruction?.toFixed(1) ?? 0}% - ${them.destruction?.toFixed(1) ?? 0}%`
          ].join('\n')
        )
        .addFields({
          name: 'Top attackers',
          value:
            us.members
              .filter((m: any) => m.attacks?.length)
              .slice(0, 15)
              .map((m: any) => `\`${pad(m.name, 15)}\` ${EMOJIS.WAR_STAR} ${m.attacks[0].stars} • ${m.attacks[0].destruction}%`)
              .join('\n') || '_no attacks yet_'
        });
      return interaction.editReply({ embeds: [embed] });
    }
    return interaction.editReply('Could not find an active CWL round for this clan.');
  }
}
