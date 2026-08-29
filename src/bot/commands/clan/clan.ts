import { AutocompleteInteraction, SlashCommandBuilder, type ChatInputCommandInteraction } from 'discord.js';
import { Command } from '../../struct/Command.js';
import { baseEmbed } from '../../../util/embeds.js';
import { EMOJIS } from '../../../util/emojis.js';

export default class ClanCommand extends Command {
  public constructor() {
    super('clan', { category: 'clan', description: "Show a clan's overview and details.", defer: true });
  }

  public builder() {
    return new SlashCommandBuilder()
      .setName('clan')
      .setDescription("Show a clan's overview and details.")
      .addStringOption((opt) =>
        opt
          .setName('tag')
          .setDescription('Clan tag or alias. Defaults to this server’s linked clan.')
          .setAutocomplete(true)
      );
  }

  public async autocomplete(interaction: AutocompleteInteraction, args: Record<string, any>) {
    const choices = await this.client.resolver.clanAutocomplete(interaction.guildId, String(args.tag ?? ''));
    await interaction.respond(choices);
  }

  public async exec(interaction: ChatInputCommandInteraction, args: Record<string, any>) {
    const { data: clan, error } = await this.client.resolver.resolveClan(interaction, args.tag);
    if (!clan) return interaction.editReply(error!);

    const embed = baseEmbed(this.client, interaction)
      .setTitle(`${clan.name} (${clan.tag})`)
      .setURL(`https://link.clashofclans.com/en?action=OpenClanProfile&tag=${encodeURIComponent(clan.tag)}`)
      .setDescription(clan.description || '_No description._')
      .addFields(
        { name: 'Level', value: `${EMOJIS.XP} ${clan.level}`, inline: true },
        { name: 'Members', value: `${EMOJIS.PEOPLE} ${clan.memberCount}/50`, inline: true },
        { name: 'Points', value: `${EMOJIS.TROPHY} ${clan.points}`, inline: true },
        { name: 'Required Trophies', value: `${EMOJIS.TROPHY} ${clan.requiredTrophies}`, inline: true },
        { name: 'War Wins', value: `${EMOJIS.SWORD} ${clan.warWins ?? 0}`, inline: true },
        { name: 'Win Streak', value: `${EMOJIS.FIRE} ${clan.warWinStreak ?? 0}`, inline: true },
        {
          name: 'War League',
          value: `${clan.warLeague?.name ?? 'Unranked'}`,
          inline: true
        },
        {
          name: 'War Log',
          value: clan.isWarLogPublic ? 'Public' : 'Private',
          inline: true
        },
        {
          name: 'Type',
          value: clan.type === 'inviteOnly' ? 'Invite Only' : clan.type === 'open' ? 'Anyone Can Join' : 'Closed',
          inline: true
        }
      );

    if (clan.location?.name) embed.addFields({ name: 'Location', value: `📍 ${clan.location.name}`, inline: true });

    return interaction.editReply({ embeds: [embed] });
  }
}
