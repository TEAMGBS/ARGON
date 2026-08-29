import { AttachmentBuilder, AutocompleteInteraction, SlashCommandBuilder, type ChatInputCommandInteraction } from 'discord.js';
import { Command } from '../../struct/Command.js';

/** Export a clan's member roster as a CSV attachment. */
export default class ExportMembersCommand extends Command {
  public constructor() {
    super('export-members', { category: 'export', description: 'Export a clan’s members as CSV.', defer: true });
  }

  public builder() {
    return new SlashCommandBuilder()
      .setName('export-members')
      .setDescription('Export a clan’s members as CSV.')
      .addStringOption((opt) => opt.setName('tag').setDescription('Clan tag or alias.').setAutocomplete(true));
  }

  public async autocomplete(interaction: AutocompleteInteraction, args: Record<string, any>) {
    await interaction.respond(await this.client.resolver.clanAutocomplete(interaction.guildId, String(args.tag ?? '')));
  }

  private csvField(value: string | number): string {
    const s = String(value);
    return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
  }

  public async exec(interaction: ChatInputCommandInteraction, args: Record<string, any>) {
    const { data: clan, error } = await this.client.resolver.resolveClan(interaction, args.tag);
    if (!clan) return interaction.editReply(error!);

    const header = ['Name', 'Tag', 'Role', 'TownHall', 'Trophies', 'Donations', 'Received', 'League'];
    const players = await Promise.all(clan.members.map((m) => this.client.coc.getPlayer(m.tag)));

    const rows = clan.members.map((m, i) => {
      const p = players[i];
      return [
        m.name,
        m.tag,
        m.role,
        p?.townHallLevel ?? m.townHallLevel,
        m.trophies,
        m.donations,
        m.received,
        p?.leagueTier?.name ?? m.leagueTier?.name ?? ''
      ]
        .map((v) => this.csvField(v as string | number))
        .join(',');
    });

    const csv = [header.join(','), ...rows].join('\n');
    const file = new AttachmentBuilder(Buffer.from(csv, 'utf8'), {
      name: `${clan.tag.replace('#', '')}-members.csv`
    });

    return interaction.editReply({ content: `${clan.name} — ${clan.memberCount} members exported.`, files: [file] });
  }
}
