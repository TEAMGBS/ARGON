/** Static constants and lookup tables used across the bot. */

/** Default embed color if a guild hasn't set its own (overridden by EMBED_COLOR env). */
export const DEFAULT_COLOR = 0x5865f2;

export const Colors = {
  RED: 0xed4245,
  GREEN: 0x57f287,
  YELLOW: 0xfee75c,
  BLURPLE: 0x5865f2,
  GREY: 0x9ba7b4
} as const;

/** Elixir/dark/hero labels used when rendering unit tables. */
export const UnitCategory = {
  HERO: 'hero',
  TROOP: 'troop',
  SPELL: 'spell',
  SIEGE: 'siege',
  PET: 'pet'
} as const;

/** Maximum members in a clan. */
export const MAX_CLAN_SIZE = 50;

/** Clash of Clans season resets on the last Monday of each month. */
export function getSeasonId(date = new Date()): string {
  const d = new Date(Date.UTC(date.getUTCFullYear(), date.getUTCMonth(), date.getUTCDate()));
  // Find the last Monday of this month.
  const lastDay = new Date(Date.UTC(d.getUTCFullYear(), d.getUTCMonth() + 1, 0));
  const lastMonday = new Date(lastDay);
  lastMonday.setUTCDate(lastDay.getUTCDate() - ((lastDay.getUTCDay() + 6) % 7));
  // Before the reset day, we're still in the previous season.
  let year = d.getUTCFullYear();
  let month = d.getUTCMonth();
  if (d.getUTCDate() < lastMonday.getUTCDate()) {
    month -= 1;
    if (month < 0) {
      month = 11;
      year -= 1;
    }
  }
  return `${year}-${String(month + 1).padStart(2, '0')}`;
}

/** Town Hall level -> emoji placeholder (replace ids with real guild emojis). */
export const TOWN_HALLS: Record<number, string> = {
  1: 'TH1',
  2: 'TH2',
  3: 'TH3',
  4: 'TH4',
  5: 'TH5',
  6: 'TH6',
  7: 'TH7',
  8: 'TH8',
  9: 'TH9',
  10: 'TH10',
  11: 'TH11',
  12: 'TH12',
  13: 'TH13',
  14: 'TH14',
  15: 'TH15',
  16: 'TH16',
  17: 'TH17'
};

/** Clan role -> display label. */
export const CLAN_ROLES: Record<string, string> = {
  leader: 'Leader',
  coLeader: 'Co-Leader',
  admin: 'Elder',
  member: 'Member'
};

/** War state -> human label. */
export const WAR_STATE: Record<string, string> = {
  notInWar: 'Not in War',
  preparation: 'Preparation Day',
  inWar: 'Battle Day',
  warEnded: 'War Ended'
};
