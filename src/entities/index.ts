/**
 * MongoDB document interfaces and collection names.
 *
 * These describe the operational data model that backs the bot: linked clans, player links,
 * per-guild settings, reminders, flags and aliases, plus the snapshots the feed poller diffs against.
 */
import type { ObjectId } from 'mongodb';

export const Collections = {
  GUILD_SETTINGS: 'guildSettings',
  CLAN_STORES: 'clanStores',
  PLAYER_LINKS: 'playerLinks',
  USERS: 'users',
  REMINDERS: 'reminders',
  REMINDER_LOGS: 'reminderLogs',
  FLAGS: 'flags',
  ALIASES: 'aliases',
  CLAN_SNAPSHOTS: 'clanSnapshots'
} as const;

/** Kinds of per-clan logs a server can enable. */
export const LogType = {
  MEMBER_LOG: 'memberLog',
  DONATION_LOG: 'donationLog',
  CLAN_FEED: 'clanFeed'
} as const;

export type LogTypeValue = (typeof LogType)[keyof typeof LogType];

export interface GuildSettings {
  _id?: ObjectId;
  guildId: string;
  /** Hex color (without leading #) used for embeds in this guild. */
  color?: string;
  /** IANA timezone id used when rendering times for this guild. */
  timezone?: string;
  locale?: string;
  createdAt: Date;
  updatedAt: Date;
}

export interface ClanLogChannel {
  type: LogTypeValue;
  channelId: string;
  webhookId?: string;
  webhookToken?: string;
}

export interface ClanStore {
  _id?: ObjectId;
  guildId: string;
  tag: string;
  name: string;
  /** Optional short alias used to reference this clan in commands. */
  alias?: string;
  /** Category/group label for organizing many clans. */
  category?: string;
  logs: ClanLogChannel[];
  /** Discord role granted to verified members of this clan. */
  memberRoleId?: string;
  createdAt: Date;
  updatedAt: Date;
}

export interface PlayerLink {
  _id?: ObjectId;
  userId: string;
  tag: string;
  name: string;
  /** True when ownership was proven with the in-game API token (via /verify). */
  verified: boolean;
  /** The first account linked by a user is their default. */
  order: number;
  createdAt: Date;
}

export interface UserInfo {
  _id?: ObjectId;
  userId: string;
  username?: string;
  timezone?: string;
  updatedAt: Date;
}

export const ReminderType = {
  WAR: 'war',
  CWL: 'cwl',
  CAPITAL: 'capital'
} as const;

export type ReminderTypeValue = (typeof ReminderType)[keyof typeof ReminderType];

export interface Reminder {
  _id?: ObjectId;
  guildId: string;
  channelId: string;
  type: ReminderTypeValue;
  /** Clan tags this reminder applies to. */
  clanTags: string[];
  /** Minutes before the event ends to fire (e.g. 60 = 1 hour before war end). */
  minutesBefore: number;
  /** Message body sent when the reminder fires. */
  message: string;
  /** Only remind members who still have this many attacks (or more) remaining. */
  minRemaining: number;
  roleId?: string;
  createdAt: Date;
}

/** Marks a reminder as already fired for a given war so we don't double-post. */
export interface ReminderLog {
  _id?: ObjectId;
  reminderId: ObjectId;
  key: string;
  firedAt: Date;
}

export interface Flag {
  _id?: ObjectId;
  guildId: string;
  tag: string;
  name: string;
  reason: string;
  flaggedBy: string;
  createdAt: Date;
}

export interface Alias {
  _id?: ObjectId;
  guildId: string;
  name: string;
  tag: string;
  createdAt: Date;
}

/** Last-seen clan member roster, used by the feed poller to detect join/leave & donation deltas. */
export interface ClanSnapshot {
  _id?: ObjectId;
  guildId: string;
  tag: string;
  members: Record<
    string,
    {
      name: string;
      role: string;
      donations: number;
      donationsReceived: number;
    }
  >;
  updatedAt: Date;
}
