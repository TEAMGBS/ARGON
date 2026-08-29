import { SlashCommandBuilder, type ChatInputCommandInteraction } from 'discord.js';
import { Command } from '../../struct/Command.js';
import { baseEmbed } from '../../../util/embeds.js';
import { EMOJIS } from '../../../util/emojis.js';

export default class PlayerCommand extends Command {
  public constructor() {
    super('player', { category: 'player', description: "Show a player's profile and stats.", defer: true });
  }

  public builder() {
    return new SlashCommandBuilder()
      .setName('player')
      .setDescription("Show a player's profile and stats.")
      .addStringOption((opt) => opt.setName('tag').setDescription('Player tag (e.g. #2PP). Defaults to your linked account.'))
      .addUserOption((opt) => opt.setName('user').setDescription('Show the linked account of another user.'));
  }

  public async exec(interaction: ChatInputCommandInteraction, args: Record<string, any>) {
    const { data: player, error } = await this.client.resolver.resolvePlayer(interaction, args.tag, args.user);
    if (!player) return interaction.editReply(error!);

    const heroes = player.heroes
      .filter((h) => h.village === 'home')
      .map((h) => `${EMOJIS.HERO} ${h.name}: **${h.level}**/${h.maxLevel}`)
      .join('\n');

    const embed = baseEmbed(this.client, interaction)
      .setTitle(`${player.name} (${player.tag})`)
      .setURL(`https://link.clashofclans.com/en?action=OpenPlayerProfile&tag=${encodeURIComponent(player.tag)}`)
      .addFields(
        { name: 'Town Hall', value: `${EMOJIS.TOWN_HALL} ${player.townHallLevel}`, inline: true },
        { name: 'XP Level', value: `${EMOJIS.XP} ${player.expLevel}`, inline: true },
        { name: 'Trophies', value: `${EMOJIS.TROPHY} ${player.trophies} (best ${player.bestTrophies})`, inline: true },
        { name: 'War Stars', value: `${EMOJIS.WAR_STAR} ${player.warStars}`, inline: true },
        { name: 'Attacks Won', value: `${EMOJIS.SWORD} ${player.attackWins}`, inline: true },
        { name: 'Defenses Won', value: `${EMOJIS.SHIELD} ${player.defenseWins}`, inline: true }
      );

    if (player.clan) {
      embed.addFields({
        name: 'Clan',
        value: `${EMOJIS.CLAN} ${player.clan.name} (${player.clan.tag}) — ${player.role ?? 'member'}`
      });
    }
    if (heroes) embed.addFields({ name: 'Heroes', value: heroes });

    embed.addFields({
      name: 'Donations',
      value: `${EMOJIS.DONATE} ${player.donations} • ${EMOJIS.RECEIVE} ${player.received}`,
      inline: true
    });

    return interaction.editReply({ embeds: [embed] });
  }
}
