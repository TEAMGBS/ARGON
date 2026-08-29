import { EmbedBuilder, type ChatInputCommandInteraction } from 'discord.js';
import type { Client } from '../bot/struct/Client.js';

/** Create an embed pre-colored for the current guild. */
export function baseEmbed(client: Client, interaction: ChatInputCommandInteraction): EmbedBuilder {
  return new EmbedBuilder().setColor(client.settings.color(interaction.guildId));
}

/** Reply or edit-reply depending on whether the interaction was deferred. */
export async function respond(
  interaction: ChatInputCommandInteraction,
  payload: Parameters<ChatInputCommandInteraction['editReply']>[0]
) {
  if (interaction.deferred || interaction.replied) return interaction.editReply(payload as any);
  return interaction.reply(payload as any);
}
