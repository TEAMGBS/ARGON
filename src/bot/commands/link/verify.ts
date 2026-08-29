import { MessageFlags, SlashCommandBuilder, type ChatInputCommandInteraction } from 'discord.js';
import { Command } from '../../struct/Command.js';
import { EMOJIS } from '../../../util/emojis.js';
import { isValidTag, normalizeTag } from '../../../util/helper.js';

/**
 * Prove ownership of an account using the in-game API token
 * (Settings → More Settings → API Token). A verified link is trusted for role assignment.
 */
export default class VerifyCommand extends Command {
  public constructor() {
    super('verify', { category: 'link', description: 'Verify ownership of a linked account.' });
  }

  public builder() {
    return new SlashCommandBuilder()
      .setName('verify')
      .setDescription('Verify ownership of a Clash of Clans account.')
      .addStringOption((opt) => opt.setName('tag').setDescription('Player tag.').setRequired(true))
      .addStringOption((opt) =>
        opt.setName('token').setDescription('In-game API token (Settings → More Settings → API Token).').setRequired(true)
      );
  }

  public async exec(interaction: ChatInputCommandInteraction, args: Record<string, any>) {
    if (!isValidTag(args.tag)) {
      return interaction.reply({ content: 'That is not a valid player tag.', flags: MessageFlags.Ephemeral });
    }
    await interaction.deferReply({ flags: MessageFlags.Ephemeral });
    const tag = normalizeTag(args.tag);

    const ok = await this.client.coc.verifyPlayerToken(tag, String(args.token).trim());
    if (!ok) return interaction.editReply(`${EMOJIS.CROSS} Verification failed. Double-check the tag and API token.`);

    const player = await this.client.coc.getPlayer(tag);
    const count = await this.client.db.playerLinks.countDocuments({ userId: interaction.user.id });
    await this.client.db.playerLinks.updateOne(
      { userId: interaction.user.id, tag },
      {
        $set: { verified: true, name: player?.name ?? tag },
        $setOnInsert: { userId: interaction.user.id, tag, order: count, createdAt: new Date() }
      },
      { upsert: true }
    );

    return interaction.editReply(`${EMOJIS.CHECK} Verified ownership of **${player?.name ?? tag}** (\`${tag}\`).`);
  }
}
