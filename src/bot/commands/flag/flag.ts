import {
  MessageFlags,
  PermissionFlagsBits,
  SlashCommandBuilder,
  type ChatInputCommandInteraction
} from 'discord.js';
import { Command } from '../../struct/Command.js';
import { baseEmbed } from '../../../util/embeds.js';
import { EMOJIS } from '../../../util/emojis.js';
import { isValidTag, normalizeTag } from '../../../util/helper.js';

/** Flag players (e.g. banned/watchlist) so staff are warned when they appear. */
export default class FlagCommand extends Command {
  public constructor() {
    super('flag', {
      category: 'flag',
      description: 'Flag players for monitoring.',
      guildOnly: true,
      userPermissions: [PermissionFlagsBits.ManageGuild]
    });
  }

  public builder() {
    return new SlashCommandBuilder()
      .setName('flag')
      .setDescription('Flag players for monitoring.')
      .setDefaultMemberPermissions(PermissionFlagsBits.ManageGuild)
      .addSubcommand((sub) =>
        sub
          .setName('create')
          .setDescription('Flag a player.')
          .addStringOption((opt) => opt.setName('tag').setDescription('Player tag.').setRequired(true))
          .addStringOption((opt) => opt.setName('reason').setDescription('Reason for the flag.').setRequired(true))
      )
      .addSubcommand((sub) =>
        sub
          .setName('delete')
          .setDescription('Remove a flag.')
          .addStringOption((opt) => opt.setName('tag').setDescription('Player tag.').setRequired(true))
      )
      .addSubcommand((sub) => sub.setName('list').setDescription('List flagged players.'));
  }

  public async exec(interaction: ChatInputCommandInteraction, args: Record<string, any>) {
    const guildId = interaction.guildId!;
    switch (args.subcommand) {
      case 'create': {
        if (!isValidTag(args.tag)) return interaction.reply({ content: 'Invalid player tag.', flags: MessageFlags.Ephemeral });
        await interaction.deferReply();
        const tag = normalizeTag(args.tag);
        const player = await this.client.coc.getPlayer(tag);
        await this.client.db.flags.updateOne(
          { guildId, tag },
          {
            $set: { name: player?.name ?? tag, reason: String(args.reason), flaggedBy: interaction.user.id },
            $setOnInsert: { guildId, tag, createdAt: new Date() }
          },
          { upsert: true }
        );
        return interaction.editReply(`${EMOJIS.CHECK} Flagged **${player?.name ?? tag}** (\`${tag}\`).`);
      }
      case 'delete': {
        const tag = normalizeTag(args.tag);
        const res = await this.client.db.flags.deleteOne({ guildId, tag });
        return interaction.reply(res.deletedCount ? `${EMOJIS.CHECK} Removed flag on \`${tag}\`.` : `No flag on \`${tag}\`.`);
      }
      default: {
        const flags = await this.client.db.flags.find({ guildId }).toArray();
        if (!flags.length) return interaction.reply('No flagged players.');
        const embed = baseEmbed(this.client, interaction)
          .setTitle('Flagged Players')
          .setDescription(
            flags.map((f) => `${EMOJIS.CROSS} **${f.name}** \`${f.tag}\` — ${f.reason} (by <@${f.flaggedBy}>)`).join('\n').slice(0, 4000)
          );
        return interaction.reply({ embeds: [embed] });
      }
    }
  }
}
