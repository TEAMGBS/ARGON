import { MessageFlags, SlashCommandBuilder, type ChatInputCommandInteraction } from 'discord.js';
import { Command } from '../../struct/Command.js';
import { baseEmbed } from '../../../util/embeds.js';
import { EMOJIS } from '../../../util/emojis.js';
import { isValidTag, normalizeTag } from '../../../util/helper.js';

/** Link, list and unlink Clash of Clans accounts to Discord users. */
export default class LinkCommand extends Command {
  public constructor() {
    super('link', { category: 'link', description: 'Link a Clash of Clans account to your Discord.' });
  }

  public builder() {
    return new SlashCommandBuilder()
      .setName('link')
      .setDescription('Link Clash of Clans accounts to Discord.')
      .addSubcommand((sub) =>
        sub
          .setName('create')
          .setDescription('Link a player tag to yourself or another user.')
          .addStringOption((opt) => opt.setName('tag').setDescription('Player tag (e.g. #2PP0).').setRequired(true))
          .addUserOption((opt) => opt.setName('user').setDescription('Link on behalf of another user (admin).'))
      )
      .addSubcommand((sub) =>
        sub
          .setName('list')
          .setDescription('List linked accounts.')
          .addUserOption((opt) => opt.setName('user').setDescription('User to list (defaults to you).'))
      )
      .addSubcommand((sub) =>
        sub
          .setName('delete')
          .setDescription('Unlink a player tag.')
          .addStringOption((opt) => opt.setName('tag').setDescription('Player tag to unlink.').setRequired(true))
      );
  }

  public async exec(interaction: ChatInputCommandInteraction, args: Record<string, any>) {
    switch (args.subcommand) {
      case 'create':
        return this.create(interaction, args);
      case 'list':
        return this.list(interaction, args);
      case 'delete':
        return this.remove(interaction, args);
      default:
        return interaction.reply({ content: 'Unknown subcommand.', flags: MessageFlags.Ephemeral });
    }
  }

  private async create(interaction: ChatInputCommandInteraction, args: Record<string, any>) {
    if (!isValidTag(args.tag)) {
      return interaction.reply({ content: 'That is not a valid player tag.', flags: MessageFlags.Ephemeral });
    }
    await interaction.deferReply({ flags: MessageFlags.Ephemeral });
    const tag = normalizeTag(args.tag);
    const player = await this.client.coc.getPlayer(tag);
    if (!player) return interaction.editReply(`No player found for \`${tag}\`.`);

    const userId = args.user ?? interaction.user.id;
    const existing = await this.client.db.playerLinks.findOne({ userId, tag });
    if (existing) return interaction.editReply(`\`${tag}\` is already linked to <@${userId}>.`);

    const count = await this.client.db.playerLinks.countDocuments({ userId });
    await this.client.db.playerLinks.insertOne({
      userId,
      tag,
      name: player.name,
      verified: false,
      order: count,
      createdAt: new Date()
    });

    return interaction.editReply(`${EMOJIS.CHECK} Linked **${player.name}** (\`${tag}\`) to <@${userId}>.`);
  }

  private async list(interaction: ChatInputCommandInteraction, args: Record<string, any>) {
    await interaction.deferReply({ flags: MessageFlags.Ephemeral });
    const userId = args.user ?? interaction.user.id;
    const links = await this.client.db.playerLinks.find({ userId }).sort({ order: 1 }).toArray();
    if (!links.length) return interaction.editReply(`<@${userId}> has no linked accounts. Use \`/link create\`.`);

    const embed = baseEmbed(this.client, interaction)
      .setTitle('Linked Accounts')
      .setDescription(
        links
          .map((l) => `${l.verified ? EMOJIS.CHECK : '•'} **${l.name}** \`${l.tag}\`${l.order === 0 ? ' _(default)_' : ''}`)
          .join('\n')
      );
    return interaction.editReply({ embeds: [embed] });
  }

  private async remove(interaction: ChatInputCommandInteraction, args: Record<string, any>) {
    await interaction.deferReply({ flags: MessageFlags.Ephemeral });
    const tag = normalizeTag(args.tag);
    const res = await this.client.db.playerLinks.deleteOne({ userId: interaction.user.id, tag });
    if (!res.deletedCount) return interaction.editReply(`\`${tag}\` was not linked to you.`);
    return interaction.editReply(`${EMOJIS.CHECK} Unlinked \`${tag}\`.`);
  }
}
