import { AutocompleteInteraction, SlashCommandBuilder, type ChatInputCommandInteraction } from 'discord.js';
import { Command } from '../../struct/Command.js';
import { baseEmbed } from '../../../util/embeds.js';
import { EMOJIS } from '../../../util/emojis.js';
import { relativeTimestamp } from '../../../util/helper.js';

/** Members who still have attacks left in the current war. */
export default class RemainingCommand extends Command {
  public constructor() {
    super('remaining', { category: 'war', description: 'Show remaining war attacks.', defer: true });
  }

  public builder() {
    return new SlashCommandBuilder()
      .setName('remaining')
      .setDescription('Show remaining war attacks.')
      .addStringOption((opt) => opt.setName('tag').setDescription('Clan tag or alias.').setAutocomplete(true));
  }

  public async autocomplete(interaction: AutocompleteInteraction, args: Record<string, any>) {
    await interaction.respond(await this.client.resolver.clanAutocomplete(interaction.guildId, String(args.tag ?? '')));
  }

  public async exec(interaction: ChatInputCommandInteraction, args: Record<string, any>) {
    const { data: clan, error } = await this.client.resolver.resolveClan(interaction, args.tag);
    if (!clan) return interaction.editReply(error!);

    const war = await this.client.coc.getCurrentWar(clan.tag);
    if (!war || war.state === 'notInWar') return interaction.editReply('Clan is not currently in a war.');
    const w = war as any;
    const perMember = w.attacksPerMember ?? 2;

    const lines = w.clan.members
      .map((m: any) => ({ m, used: m.attacks?.length ?? 0 }))
      .filter((x: any) => x.used < perMember)
      .sort((a: any, b: any) => a.m.mapPosition - b.m.mapPosition)
      .map((x: any) => `${EMOJIS.SWORD} **${x.m.name}** — ${perMember - x.used} left`);

    const embed = baseEmbed(this.client, interaction)
      .setTitle(`${w.clan.name} — Remaining Attacks`)
      .setDescription(lines.length ? lines.join('\n').slice(0, 4000) : 'All attacks used! 🎉');

    if (w.state === 'inWar') embed.setFooter({ text: 'War ends' }).setTimestamp(w.endTime);
    else embed.addFields({ name: 'Battle day', value: relativeTimestamp(w.startTime) });

    return interaction.editReply({ embeds: [embed] });
  }
}
