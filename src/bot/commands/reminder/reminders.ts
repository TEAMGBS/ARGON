import {
  ChannelType,
  MessageFlags,
  PermissionFlagsBits,
  SlashCommandBuilder,
  type ChatInputCommandInteraction
} from 'discord.js';
import { Command } from '../../struct/Command.js';
import { baseEmbed } from '../../../util/embeds.js';
import { EMOJIS } from '../../../util/emojis.js';
import { ReminderType } from '../../../entities/index.js';
import { isValidTag, normalizeTag } from '../../../util/helper.js';

/** War reminders — fired by the background Scheduler for members who still have attacks left. */
export default class RemindersCommand extends Command {
  public constructor() {
    super('reminders', {
      category: 'reminder',
      description: 'Manage war reminders.',
      guildOnly: true,
      userPermissions: [PermissionFlagsBits.ManageGuild]
    });
  }

  public builder() {
    return new SlashCommandBuilder()
      .setName('reminders')
      .setDescription('Manage war reminders.')
      .setDefaultMemberPermissions(PermissionFlagsBits.ManageGuild)
      .addSubcommand((sub) =>
        sub
          .setName('create')
          .setDescription('Create a war reminder.')
          .addIntegerOption((opt) =>
            opt.setName('before').setDescription('Minutes before war end to fire.').setRequired(true).setMinValue(5).setMaxValue(1440)
          )
          .addStringOption((opt) => opt.setName('tag').setDescription('Clan tag.').setRequired(true))
          .addChannelOption((opt) =>
            opt.setName('channel').setDescription('Channel to post in.').addChannelTypes(ChannelType.GuildText).setRequired(true)
          )
          .addStringOption((opt) => opt.setName('message').setDescription('Custom message.'))
          .addIntegerOption((opt) =>
            opt.setName('min_remaining').setDescription('Only ping members with at least this many attacks left.').setMinValue(1).setMaxValue(2)
          )
          .addRoleOption((opt) => opt.setName('role').setDescription('Role to mention.'))
      )
      .addSubcommand((sub) => sub.setName('list').setDescription('List war reminders.'))
      .addSubcommand((sub) =>
        sub
          .setName('delete')
          .setDescription('Delete a reminder by its number (from /reminders list).')
          .addIntegerOption((opt) => opt.setName('index').setDescription('Reminder number.').setRequired(true).setMinValue(1))
      );
  }

  public async exec(interaction: ChatInputCommandInteraction, args: Record<string, any>) {
    const guildId = interaction.guildId!;
    switch (args.subcommand) {
      case 'create': {
        if (!isValidTag(args.tag)) {
          return interaction.reply({ content: 'Invalid clan tag.', flags: MessageFlags.Ephemeral });
        }
        await this.client.db.reminders.insertOne({
          guildId,
          channelId: args.channel,
          type: ReminderType.WAR,
          clanTags: [normalizeTag(args.tag)],
          minutesBefore: args.before,
          message: args.message ?? 'You still have war attacks remaining!',
          minRemaining: args.min_remaining ?? 1,
          roleId: args.role ?? undefined,
          createdAt: new Date()
        });
        return interaction.reply(
          `${EMOJIS.CHECK} War reminder created: **${args.before} min** before war end for \`${normalizeTag(args.tag)}\` in <#${args.channel}>.`
        );
      }
      case 'delete': {
        const reminders = await this.client.db.reminders.find({ guildId }).sort({ createdAt: 1 }).toArray();
        const target = reminders[args.index - 1];
        if (!target) return interaction.reply({ content: 'No reminder with that number.', flags: MessageFlags.Ephemeral });
        await this.client.db.reminders.deleteOne({ _id: target._id });
        return interaction.reply(`${EMOJIS.CHECK} Deleted reminder #${args.index}.`);
      }
      default: {
        const reminders = await this.client.db.reminders.find({ guildId }).sort({ createdAt: 1 }).toArray();
        if (!reminders.length) return interaction.reply('No reminders configured. Create one with `/reminders create`.');
        const embed = baseEmbed(this.client, interaction)
          .setTitle('War Reminders')
          .setDescription(
            reminders
              .map(
                (r, i) =>
                  `**${i + 1}.** ${r.minutesBefore}m before • \`${r.clanTags.join(', ')}\` → <#${r.channelId}>${r.roleId ? ` • <@&${r.roleId}>` : ''}`
              )
              .join('\n')
          );
        return interaction.reply({ embeds: [embed] });
      }
    }
  }
}
