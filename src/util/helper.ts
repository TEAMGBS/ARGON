/** Small formatting & tag helpers shared across commands. */
import moment from 'moment';
import 'moment-duration-format';

/** Normalize a Clash of Clans tag: uppercase, strip spaces, ensure a single leading '#'. */
export function normalizeTag(input: string): string {
  const tag = input
    .toUpperCase()
    .replace(/O/g, '0')
    .replace(/[^0-9A-Z]/g, '');
  return `#${tag}`;
}

/** True if the string looks like a valid CoC tag once normalized. */
export function isValidTag(input: string): boolean {
  const tag = normalizeTag(input);
  return /^#[0-9A-Z]{3,12}$/.test(tag);
}

/** URL-safe encoding of a tag for API paths (# -> %23). */
export function encodeTag(tag: string): string {
  return encodeURIComponent(normalizeTag(tag));
}

/** Humanize a duration given in milliseconds, e.g. "2d 3h 10m". */
export function duration(ms: number): string {
  if (ms <= 0) return '0m';
  return moment.duration(ms).format('d[d] h[h] m[m]', { trim: 'both mid' });
}

/** Relative Discord timestamp, e.g. <t:1700000000:R>. */
export function relativeTimestamp(date: Date | string | number): string {
  const unix = Math.floor(new Date(date).getTime() / 1000);
  return `<t:${unix}:R>`;
}

/** Absolute short Discord timestamp. */
export function shortTimestamp(date: Date | string | number): string {
  const unix = Math.floor(new Date(date).getTime() / 1000);
  return `<t:${unix}:f>`;
}

/** Right-pad/truncate a string to a fixed column width (monospace tables). */
export function pad(value: string | number, width: number): string {
  const s = String(value);
  return s.length >= width ? s.slice(0, width) : s + ' '.repeat(width - s.length);
}

/** Left-pad a number for aligned columns. */
export function padStart(value: string | number, width: number): string {
  return String(value).padStart(width);
}

/** Split an array into chunks of at most `size`. */
export function chunk<T>(arr: T[], size: number): T[][] {
  const out: T[][] = [];
  for (let i = 0; i < arr.length; i += size) out.push(arr.slice(i, i + size));
  return out;
}

/** CoC API dates look like 20240102T030405.000Z — turn them into a Date. */
export function parseCocDate(value: string): Date {
  const iso = value.replace(/^(\d{4})(\d{2})(\d{2})T(\d{2})(\d{2})(\d{2})\.\d{3}Z$/, '$1-$2-$3T$4:$5:$6.000Z');
  return new Date(iso);
}
