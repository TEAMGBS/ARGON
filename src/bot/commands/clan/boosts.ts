import { AutocompleteInteraction, SlashCommandBuilder, type ChatInputCommandInteraction } from 'discord.js';
import { Command } from '../../struct/Command.js';
import { baseEmbed } from '../../../util/embeds.js';
import { EMOJIS } from '../../../util/emojis.js';

/** Shows Super Troop boosts active among a clan's members. */
export default class BoostsCommand extends Command {
  public constructor() {
    super('boosts', { category: 'clan', description: 'Show active Super Troop boosts in a clan.', defer: true });
  }

  public builder() {
    return new SlashCommandBuilder()
      .setName('boosts')
      .setDescription('Show active Super Troop boosts in a clan.')
      .addStringOption((opt) => opt.setName('tag').setDescription('Clan tag or alias.').setAutocomplete(true));
  }

  public async autocomplete(interaction: AutocompleteInteraction, args: Record<string, any>) {
    await interaction.respond(await this.client.resolver.clanAutocomplete(interaction.guildId, String(args.tag ?? '')));
  }

  public async exec(interaction: ChatInputCommandInteraction, args: Record<string, any>) {
    const { data: clan, error } = await this.client.resolver.resolveClan(interaction, args.tag);
    if (!clan) return interaction.editReply(error!);

    const players = await Promise.all(clan.members.map((m) => this.client.coc.getPlayer(m.tag)));
    const boostMap = new Map<string, string[]>();
    for (const p of players) {
      if (!p) continue;
      const active = p.troops.filter((t) => t.isSuperTroop && t.isActive);
      for (const t of active) {
        const list = boostMap.get(t.name) ?? [];
        list.push(p.name);
        boostMap.set(t.name, list);
      }
    }

    const embed = baseEmbed(this.client, interaction).setTitle(`${clan.name} (${clan.tag}) — Active Boosts`);
    if (!boostMap.size) {
      embed.setDescription('No active Super Troop boosts right now.');
    } else {
      embed.setDescription(
        [...boostMap.entries()]
          .map(([troop, names]) => `${EMOJIS.TROOP} **${troop}** — ${names.length}\n${names.map((n) => `• ${n}`).join('\n')}`)
          .join('\n\n')
          .slice(0, 4000)
      );
    }

    return interaction.editReply({ embeds: [embed] });
  }
}
