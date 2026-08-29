import { EmbedBuilder, type TextChannel } from 'discord.js';
import type { ObjectId } from 'mongodb';
import { LogType, type ClanStore, type Reminder } from '../../entities/index.js';
import { EMOJIS } from '../../util/emojis.js';
import { relativeTimestamp } from '../../util/helper.js';
import { Logger } from '../../util/logger.js';
import type { Client } from './Client.js';

/**
 * Background loop that (a) fires due war reminders and (b) diffs each linked clan's roster/donations
 * against the last snapshot to post member and donation feed logs. This is the simplified,
 * self-contained equivalent of ClashPerk's RPC/feed pipeline (ClickHouse/Kafka omitted for the MVP).
 */
export class Scheduler {
  private timer: NodeJS.Timeout | null = null;
  private running = false;
  private readonly log = new Logger('Scheduler');

  public constructor(private readonly client: Client) {}

  public start(): void {
    const seconds = Number(process.env.POLL_INTERVAL_SECONDS || 60);
    this.timer = setInterval(() => void this.tick(), seconds * 1000);
    this.log.info(`Scheduler started (every ${seconds}s).`);
  }

  public stop(): void {
    if (this.timer) clearInterval(this.timer);
    this.timer = null;
  }

  private async tick(): Promise<void> {
    if (this.running) return; // avoid overlap on slow API responses
    this.running = true;
    try {
      // Only one shard/cluster should own the poll cycle at a time.
      const gotLock = await this.client.redis.acquireLock('scheduler:tick', 55);
      if (!gotLock) return;

      const stores = await this.client.db.clanStores.find({}).toArray();
      for (const store of stores) {
        await this.pollClanFeed(store).catch((e) => this.log.debug('feed error', e));
      }
      await this.runReminders().catch((e) => this.log.debug('reminder error', e));
    } catch (error) {
      this.log.error('tick failed:', error);
    } finally {
      this.running = false;
    }
  }

  // ── Clan feed: member join/leave + donation deltas ────────────────────────────────────────────
  private async pollClanFeed(store: ClanStore): Promise<void> {
    const memberLog = store.logs.find((l) => l.type === LogType.MEMBER_LOG);
    const donationLog = store.logs.find((l) => l.type === LogType.DONATION_LOG);
    if (!memberLog && !donationLog) return;

    const clan = await this.client.coc.getClan(store.tag);
    if (!clan) return;

    const current: Record<string, { name: string; role: string; donations: number; donationsReceived: number }> = {};
    for (const m of clan.members) {
      current[m.tag] = {
        name: m.name,
        role: m.role,
        donations: m.donations,
        donationsReceived: m.received
      };
    }

    const snapshot = await this.client.db.clanSnapshots.findOne({ guildId: store.guildId, tag: store.tag });
    const previous = snapshot?.members ?? {};

    // First run: just record, don't spam a feed for every existing member.
    if (snapshot) {
      if (memberLog) await this.postMemberChanges(memberLog.channelId, clan.name, previous, current);
      if (donationLog) await this.postDonationChanges(donationLog.channelId, clan.name, previous, current);
    }

    await this.client.db.clanSnapshots.updateOne(
      { guildId: store.guildId, tag: store.tag },
      { $set: { members: current, updatedAt: new Date() } },
      { upsert: true }
    );
  }

  private async postMemberChanges(
    channelId: string,
    clanName: string,
    prev: Record<string, { name: string }>,
    curr: Record<string, { name: string }>
  ): Promise<void> {
    const joined = Object.keys(curr).filter((tag) => !prev[tag]);
    const left = Object.keys(prev).filter((tag) => !curr[tag]);
    if (!joined.length && !left.length) return;

    const lines = [
      ...joined.map((tag) => `${EMOJIS.UP} **${curr[tag].name}** \`${tag}\` joined`),
      ...left.map((tag) => `${EMOJIS.DOWN} **${prev[tag].name}** \`${tag}\` left`)
    ];
    const embed = new EmbedBuilder()
      .setTitle(`${EMOJIS.CLAN} ${clanName} — Member Log`)
      .setDescription(lines.join('\n').slice(0, 4000))
      .setColor(this.client.settings.color(null))
      .setTimestamp();
    await this.send(channelId, embed);
  }

  private async postDonationChanges(
    channelId: string,
    clanName: string,
    prev: Record<string, { name: string; donations: number; donationsReceived: number }>,
    curr: Record<string, { name: string; donations: number; donationsReceived: number }>
  ): Promise<void> {
    const lines: string[] = [];
    for (const tag of Object.keys(curr)) {
      const before = prev[tag];
      if (!before) continue;
      const donated = curr[tag].donations - before.donations;
      const received = curr[tag].donationsReceived - before.donationsReceived;
      if (donated > 0) lines.push(`${EMOJIS.DONATE} **${curr[tag].name}** donated \`${donated}\``);
      if (received > 0) lines.push(`${EMOJIS.RECEIVE} **${curr[tag].name}** received \`${received}\``);
    }
    if (!lines.length) return;

    const embed = new EmbedBuilder()
      .setTitle(`${EMOJIS.CLAN} ${clanName} — Donation Log`)
      .setDescription(lines.join('\n').slice(0, 4000))
      .setColor(this.client.settings.color(null))
      .setTimestamp();
    await this.send(channelId, embed);
  }

  // ── War reminders ─────────────────────────────────────────────────────────────────────────────
  private async runReminders(): Promise<void> {
    const reminders = await this.client.db.reminders.find({ type: 'war' }).toArray();
    for (const reminder of reminders) {
      for (const tag of reminder.clanTags) {
        await this.evaluateWarReminder(reminder, tag).catch((e) => this.log.debug('war reminder', e));
      }
    }
  }

  private async evaluateWarReminder(reminder: Reminder, tag: string): Promise<void> {
    const war = await this.client.coc.getCurrentWar(tag);
    if (!war || war.state !== 'inWar') return;

    // clashofclans.js exposes war times as Date objects.
    const endDate: Date = (war as any).endTime;
    const endTime = new Date(endDate).getTime();
    const now = Date.now();
    const minutesLeft = (endTime - now) / 60000;
    // Fire once when we enter the window [minutesBefore, minutesBefore - pollInterval).
    const pollMinutes = Number(process.env.POLL_INTERVAL_SECONDS || 60) / 60;
    if (minutesLeft > reminder.minutesBefore || minutesLeft < reminder.minutesBefore - pollMinutes) return;

    const key = `${tag}:${endTime}:${reminder.minutesBefore}`;
    const already = await this.client.db.reminderLogs.findOne({ reminderId: reminder._id as ObjectId, key });
    if (already) return;

    const attacksPerMember = (war as any).attacksPerMember ?? 2;
    const clanSide = (war as any).clan;
    const laggards = clanSide.members
      .filter((m: any) => attacksPerMember - (m.attacks?.length ?? 0) >= reminder.minRemaining)
      .map((m: any) => `• **${m.name}** — ${attacksPerMember - (m.attacks?.length ?? 0)} left`);

    if (!laggards.length) return;

    const embed = new EmbedBuilder()
      .setTitle(`${EMOJIS.SWORD} War Reminder — ${clanSide.name}`)
      .setDescription(
        [
          reminder.message,
          '',
          `War ends ${relativeTimestamp(new Date(endTime))}.`,
          '',
          laggards.slice(0, 40).join('\n')
        ].join('\n')
      )
      .setColor(this.client.settings.color(reminder.guildId))
      .setTimestamp();

    const content = reminder.roleId ? `<@&${reminder.roleId}>` : undefined;
    await this.send(reminder.channelId, embed, content);
    await this.client.db.reminderLogs.insertOne({ reminderId: reminder._id as ObjectId, key, firedAt: new Date() });
  }

  private async send(channelId: string, embed: EmbedBuilder, content?: string): Promise<void> {
    try {
      const channel = await this.client.channels.fetch(channelId).catch(() => null);
      if (!channel || !channel.isTextBased()) return;
      await (channel as TextChannel).send({ content, embeds: [embed] });
    } catch (error) {
      this.log.debug(`send to ${channelId} failed:`, (error as Error).message);
    }
  }
}
