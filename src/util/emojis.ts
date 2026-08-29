/**
 * Emoji placeholders.
 *
 * ClashPerk uses a large set of custom Discord emojis (troops, heroes, town halls, resources).
 * To keep this replica self-contained we use unicode/text placeholders here. Swap these for
 * `<:name:id>` custom-emoji strings uploaded to your own bot/emoji server for the full look.
 */
export const EMOJIS = {
  CLAN: '🛡️',
  TROPHY: '🏆',
  VERSUS_TROPHY: '⚔️',
  WAR_STAR: '⭐',
  SWORD: '🗡️',
  SHIELD: '🛡️',
  GOLD: '🟡',
  ELIXIR: '🟣',
  DARK_ELIXIR: '⚫',
  GEM: '💎',
  CLOCK: '⏱️',
  PEOPLE: '👥',
  CROWN: '👑',
  FIRE: '🔥',
  UP: '⬆️',
  DOWN: '⬇️',
  CHECK: '✅',
  CROSS: '❌',
  TOWN_HALL: '🏛️',
  BUILDER_HALL: '🔨',
  DONATE: '📤',
  RECEIVE: '📥',
  XP: '✨',
  CAPITAL_GOLD: '🏅',
  RAID_MEDAL: '🎖️',
  HERO: '🦸',
  TROOP: '🪖',
  SPELL: '🧪',
  SIEGE: '🚜',
  PET: '🐾'
} as const;

/** War-result star emoji row for n stars out of 3. */
export function stars(count: number): string {
  return '⭐'.repeat(Math.max(0, Math.min(3, count))) + '☆'.repeat(3 - Math.max(0, Math.min(3, count)));
}
