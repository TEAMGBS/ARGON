/** Minimal leveled logger — timestamped, level-filtered console output. */
const LEVELS = { debug: 10, info: 20, warn: 30, error: 40 } as const;
type Level = keyof typeof LEVELS;

const threshold = LEVELS[(process.env.LOG_LEVEL as Level) ?? 'info'] ?? LEVELS.info;

function emit(level: Level, label: string, args: unknown[]) {
  if (LEVELS[level] < threshold) return;
  const ts = new Date().toISOString();
  const prefix = `[${ts}] [${level.toUpperCase()}]${label ? ` [${label}]` : ''}`;
  const fn = level === 'error' ? console.error : level === 'warn' ? console.warn : console.log;
  fn(prefix, ...args);
}

export class Logger {
  public constructor(private readonly label = '') {}

  public debug(...args: unknown[]) {
    emit('debug', this.label, args);
  }
  public info(...args: unknown[]) {
    emit('info', this.label, args);
  }
  public warn(...args: unknown[]) {
    emit('warn', this.label, args);
  }
  public error(...args: unknown[]) {
    emit('error', this.label, args);
  }
}

export const logger = new Logger();
