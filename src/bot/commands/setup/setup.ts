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
import { LogType, type ClanLogChannel } from '../../../entities/index.js';
import { isValidTag, normalizeTag } from '../../../util/helper.js';

/** Link clans to a server and configure their feed/log channels. */
export default class SetupCommand extends Command {
  public constructor() {
    super('setup', {
      category: 'setup',
      description: 'Link clans and configure logs for this server.',
      guildOnly: true,
      userPermissions: [PermissionFlagsBits.ManageGuild]
    });
  }

  public builder() {
    return new SlashCommandBuilder()
      .setName('setup')
      .setDescription('Link clans and configure logs for this server.')
      .setDefaultMemberPermissions(PermissionFlagsBits.ManageGuild)
      .addSubcommand((sub) =>
        sub
          .setName('clan')
          .setDescription('Link a clan to this server.')
          .addStringOption((opt) => opt.setName('tag').setDescription('Clan tag.').setRequired(true))
          .addStringOption((opt) => opt.setName('alias').setDescription('Short alias for this clan.'))
      )
      .addSubcommand((sub) =>
        sub
          .setName('remove')
          .setDescription('Unlink a clan from this server.')
          .addStringOption((opt) => opt.setName('tag').setDescription('Clan tag.').setRequired(true))
      )
      .addSubcommand((sub) => sub.setName('list').setDescription('List clans linked to this server.'))
      .addSubcommand((sub) =>
        sub
          .setName('log')
          .setDescription('Enable a log/feed for a clan in a channel.')
          .addStringOption((opt) => opt.setName('tag').setDescription('Clan tag.').setRequired(true))
          .addStringOption((opt) =>
            opt
              .setName('type')
              .setDescription('Which log to enable.')
              .setRequired(true)
              .addChoices(
                { name: 'Member join/leave log', value: LogType.MEMBER_LOG },
                { name: 'Donation log', value: LogType.DONATION_LOG },
                { name: 'Clan feed', value: LogType.CLAN_FEED }
              )
          )
          .addChannelOption((opt) =>
            opt
              .setName('channel')
              .setDescription('Target channel.')
              .addChannelTypes(ChannelType.GuildText)
              .setRequired(true)
          )
      );
  }

  public async exec(interaction: ChatInputCommandInteraction, args: Record<string, any>) {
    switch (args.subcommand) {
      case 'clan':
        return this.addClan(interaction, args);
      case 'remove':
        return this.removeClan(interaction, args);
      case 'list':
        return this.listClans(interaction);
      case 'log':
        return this.setLog(interaction, args);
      default:
        return interaction.reply({ content: 'Unknown subcommand.', flags: MessageFlags.Ephemeral });
    }
  }

  private async addClan(interaction: ChatInputCommandInteraction, args: Record<string, any>) {
    if (!isValidTag(args.tag)) {
      return interaction.reply({ content: 'Invalid clan tag.', flags: MessageFlags.Ephemeral });
    }
    await interaction.deferReply();
    const tag = normalizeTag(args.tag);
    const clan = await this.client.coc.getClan(tag);
    if (!clan) return interaction.editReply(`No clan found for \`${tag}\`.`);

    const now = new Date();
    await this.client.db.clanStores.updateOne(
      { guildId: interaction.guildId!, tag },
      {
        $set: { name: clan.name, alias: args.alias?.toLowerCase(), updatedAt: now },
        $setOnInsert: { guildId: interaction.guildId!, tag, logs: [] as ClanLogChannel[], createdAt: now }
      },
      { upsert: true }
    );

    // Also register an alias if provided.
    if (args.alias) {
      await this.client.db.aliases.updateOne(
        { guildId: interaction.guildId!, name: args.alias.toLowerCase() },
        { $set: { tag, guildId: interaction.guildId!, name: args.alias.toLowerCase() }, $setOnInsert: { createdAt: now } },
        { upsert: true }
      );
    }

    return interaction.editReply(`${EMOJIS.CHECK} Linked **${clan.name}** (\`${tag}\`) to this server.`);
  }

  private async removeClan(interaction: ChatInputCommandInteraction, args: Record<string, any>) {
    await interaction.deferReply();
    const tag = normalizeTag(args.tag);
    const res = await this.client.db.clanStores.deleteOne({ guildId: interaction.guildId!, tag });
    await this.client.db.clanSnapshots.deleteOne({ guildId: interaction.guildId!, tag });
    if (!res.deletedCount) return interaction.editReply(`\`${tag}\` is not linked here.`);
    return interaction.editReply(`${EMOJIS.CHECK} Unlinked \`${tag}\`.`);
  }

  private async listClans(interaction: ChatInputCommandInteraction) {
    await interaction.deferReply();
    const stores = await this.client.db.clanStores.find({ guildId: interaction.guildId! }).toArray();
    if (!stores.length) return interaction.editReply('No clans linked. Add one with `/setup clan`.');

    const embed = baseEmbed(this.client, interaction)
      .setTitle('Linked Clans')
      .setDescription(
        stores
          .map((s) => {
            const logs = s.logs.map((l) => `${l.type} → <#${l.channelId}>`).join(', ') || 'no logs';
            return `${EMOJIS.CLAN} **${s.name}** (${s.tag})${s.alias ? ` \`${s.alias}\`` : ''}\n  ${logs}`;
          })
          .join('\n')
      );
    return interaction.editReply({ embeds: [embed] });
  }

  private async setLog(interaction: ChatInputCommandInteraction, args: Record<string, any>) {
    await interaction.deferReply();
    const tag = normalizeTag(args.tag);
    const store = await this.client.db.clanStores.findOne({ guildId: interaction.guildId!, tag });
    if (!store) return interaction.editReply(`\`${tag}\` is not linked. Add it with \`/setup clan\` first.`);

    const logs = store.logs.filter((l) => l.type !== args.type);
    logs.push({ type: args.type, channelId: args.channel });
    await this.client.db.clanStores.updateOne(
      { guildId: interaction.guildId!, tag },
      { $set: { logs, updatedAt: new Date() } }
    );

    return interaction.editReply(`${EMOJIS.CHECK} \`${args.type}\` for **${store.name}** → <#${args.channel}>.`);
  }
}
