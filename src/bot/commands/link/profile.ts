import { SlashCommandBuilder, type ChatInputCommandInteraction } from 'discord.js';
import { Command } from '../../struct/Command.js';
import { baseEmbed } from '../../../util/embeds.js';
import { EMOJIS } from '../../../util/emojis.js';

/** Show a Discord user's linked accounts as a combined profile card. */
export default class ProfileCommand extends Command {
  public constructor() {
    super('profile', { category: 'link', description: 'Show a member’s linked accounts profile.', defer: true });
  }

  public builder() {
    return new SlashCommandBuilder()
      .setName('profile')
      .setDescription('Show a member’s linked accounts profile.')
      .addUserOption((opt) => opt.setName('user').setDescription('User to view (defaults to you).'));
  }

  public async exec(interaction: ChatInputCommandInteraction, args: Record<string, any>) {
    const userId = args.user ?? interaction.user.id;
    const links = await this.client.db.playerLinks.find({ userId }).sort({ order: 1 }).toArray();
    if (!links.length) return interaction.editReply(`<@${userId}> has no linked accounts.`);

    const players = await Promise.all(links.map((l) => this.client.coc.getPlayer(l.tag)));
    const lines = players
      .filter(Boolean)
      .map((p, i) => {
        const verified = links[i]?.verified ? EMOJIS.CHECK : '';
        return `${verified} ${EMOJIS.TOWN_HALL} TH${p!.townHallLevel} **${p!.name}** (${p!.tag}) — ${EMOJIS.TROPHY} ${p!.trophies}${p!.clan ? ` • ${p!.clan.name}` : ''}`;
      });

    const user = await this.client.users.fetch(userId).catch(() => null);
    const embed = baseEmbed(this.client, interaction)
      .setTitle(`${user?.username ?? 'Member'} — Profile`)
      .setDescription(lines.join('\n').slice(0, 4000))
      .setThumbnail(user?.displayAvatarURL() ?? null);

    return interaction.editReply({ embeds: [embed] });
  }
}
