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

/** Short aliases that stand in for clan tags in commands. */
export default class AliasCommand extends Command {
  public constructor() {
    super('alias', {
      category: 'setup',
      description: 'Manage clan tag aliases.',
      guildOnly: true,
      userPermissions: [PermissionFlagsBits.ManageGuild]
    });
  }

  public builder() {
    return new SlashCommandBuilder()
      .setName('alias')
      .setDescription('Manage clan tag aliases.')
      .setDefaultMemberPermissions(PermissionFlagsBits.ManageGuild)
      .addSubcommand((sub) =>
        sub
          .setName('create')
          .setDescription('Create an alias for a clan tag.')
          .addStringOption((opt) => opt.setName('name').setDescription('Alias name.').setRequired(true))
          .addStringOption((opt) => opt.setName('tag').setDescription('Clan tag.').setRequired(true))
      )
      .addSubcommand((sub) =>
        sub
          .setName('delete')
          .setDescription('Delete an alias.')
          .addStringOption((opt) => opt.setName('name').setDescription('Alias name.').setRequired(true))
      )
      .addSubcommand((sub) => sub.setName('list').setDescription('List all aliases.'));
  }

  public async exec(interaction: ChatInputCommandInteraction, args: Record<string, any>) {
    const guildId = interaction.guildId!;
    switch (args.subcommand) {
      case 'create': {
        if (!isValidTag(args.tag)) {
          return interaction.reply({ content: 'Invalid clan tag.', flags: MessageFlags.Ephemeral });
        }
        const name = String(args.name).toLowerCase();
        await this.client.db.aliases.updateOne(
          { guildId, name },
          { $set: { guildId, name, tag: normalizeTag(args.tag) }, $setOnInsert: { createdAt: new Date() } },
          { upsert: true }
        );
        return interaction.reply(`${EMOJIS.CHECK} Alias \`${name}\` → \`${normalizeTag(args.tag)}\`.`);
      }
      case 'delete': {
        const name = String(args.name).toLowerCase();
        const res = await this.client.db.aliases.deleteOne({ guildId, name });
        return interaction.reply(
          res.deletedCount ? `${EMOJIS.CHECK} Deleted alias \`${name}\`.` : `No alias named \`${name}\`.`
        );
      }
      default: {
        const aliases = await this.client.db.aliases.find({ guildId }).toArray();
        if (!aliases.length) return interaction.reply('No aliases yet. Create one with `/alias create`.');
        const embed = baseEmbed(this.client, interaction)
          .setTitle('Clan Aliases')
          .setDescription(aliases.map((a) => `\`${a.name}\` → \`${a.tag}\``).join('\n'));
        return interaction.reply({ embeds: [embed] });
      }
    }
  }
}
