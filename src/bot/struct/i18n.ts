import { readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';
import i18next from 'i18next';
import { Logger } from '../../util/logger.js';

const log = new Logger('i18n');

/** Load locale JSON files and initialize i18next. Extend by dropping more files in /locales. */
export async function initI18n(): Promise<void> {
  const here = dirname(fileURLToPath(import.meta.url));
  // dist/bot/struct -> repo root/locales (works in both src via tsx and compiled dist).
  const localesDir = resolve(here, '../../../locales');

  const load = async (lng: string) => {
    try {
      const raw = await readFile(resolve(localesDir, `${lng}.json`), 'utf8');
      return JSON.parse(raw);
    } catch {
      return {};
    }
  };

  await i18next.init({
    lng: 'en',
    fallbackLng: 'en',
    resources: {
      en: { translation: await load('en') }
    },
    interpolation: { escapeValue: false }
  });

  log.info('i18n initialized.');
}

/** Translate a key with optional interpolation. */
export function t(key: string, vars?: Record<string, unknown>): string {
  return i18next.t(key, vars ?? {}) as string;
}
