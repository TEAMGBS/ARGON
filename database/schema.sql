-- ARGON database schema (Postgres / Supabase).
--
-- Applied in full on every startup by database/db.py (conn.execute(schema)).
-- Everything uses IF NOT EXISTS, so a fresh Supabase database is built entirely
-- from this one file and re-running it against an existing database is safe -
-- no follow-up migration commands required.
--
-- Discord ids are stored as BIGINT; Clash of Clans tags as TEXT (with the '#').


-- ---------------------------------------------------------------------------
-- Linked Clash of Clans accounts (Discord user <-> player tag)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS linked_accounts (
    id          SERIAL PRIMARY KEY,
    discord_id  BIGINT NOT NULL,
    tag         TEXT NOT NULL UNIQUE,
    name        TEXT,
    verified    BOOLEAN NOT NULL DEFAULT FALSE,
    linked_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_linked_accounts_discord_id ON linked_accounts(discord_id);


-- ---------------------------------------------------------------------------
-- Per-guild settings (embed color, timezone)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS guild_settings (
    guild_id    BIGINT PRIMARY KEY,
    color       TEXT,
    timezone    TEXT NOT NULL DEFAULT 'UTC',
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


-- ---------------------------------------------------------------------------
-- Clans linked to a guild
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS clan_stores (
    id          SERIAL PRIMARY KEY,
    guild_id    BIGINT NOT NULL,
    tag         TEXT NOT NULL,
    name        TEXT NOT NULL,
    category    TEXT NOT NULL DEFAULT 'casual',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (guild_id, tag)
);

-- Added after the initial release; safe to re-run on an existing database.
ALTER TABLE clan_stores ADD COLUMN IF NOT EXISTS category TEXT NOT NULL DEFAULT 'casual';

CREATE INDEX IF NOT EXISTS idx_clan_stores_guild ON clan_stores(guild_id);


-- ---------------------------------------------------------------------------
-- Per-clan log channels (member log, donation log, clan feed)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS clan_logs (
    id          SERIAL PRIMARY KEY,
    guild_id    BIGINT NOT NULL,
    tag         TEXT NOT NULL,
    log_type    TEXT NOT NULL,           -- 'member' | 'donation' | 'feed'
    channel_id  BIGINT NOT NULL,
    UNIQUE (guild_id, tag, log_type)
);

CREATE INDEX IF NOT EXISTS idx_clan_logs_guild ON clan_logs(guild_id);


-- ---------------------------------------------------------------------------
-- Last-seen clan roster snapshot (the feed poller diffs against this)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS clan_snapshots (
    guild_id    BIGINT NOT NULL,
    tag         TEXT NOT NULL,
    members     JSONB NOT NULL,          -- { tag: {name, role, donations, received} }
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (guild_id, tag)
);


-- ---------------------------------------------------------------------------
-- Reminders (war / capital / clan games), fired by the background scheduler.
-- ---------------------------------------------------------------------------
-- One-time migration: an earlier build shipped a different reminders table
-- (SERIAL id, minutes_before column). Drop it once so the richer table below
-- can be created. The guard checks for a column that only the old table has, so
-- this is a no-op on a fresh database and never runs twice.
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'reminders' AND column_name = 'minutes_before'
    ) THEN
        DROP TABLE IF EXISTS reminder_logs;
        DROP TABLE reminders;
    END IF;
END $$;

CREATE TABLE IF NOT EXISTS reminders (
    id                TEXT PRIMARY KEY,
    guild_id          BIGINT NOT NULL,
    clan_tag          TEXT NOT NULL,
    type              TEXT NOT NULL,               -- 'war' | 'capital' | 'cg'
    channel_id        BIGINT NOT NULL,
    created_by        BIGINT NOT NULL,
    message           TEXT NOT NULL DEFAULT '',
    timing_minutes    INTEGER[] NOT NULL DEFAULT '{}',
    threshold         INTEGER NOT NULL DEFAULT 0,
    remaining_filter  INTEGER[] NOT NULL DEFAULT '{}',
    member_scope      TEXT NOT NULL DEFAULT 'all', -- 'all' | 'filtered'
    townhalls         INTEGER[] NOT NULL DEFAULT '{}',
    roles             TEXT[] NOT NULL DEFAULT '{}',
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_reminders_guild ON reminders(guild_id);
CREATE INDEX IF NOT EXISTS idx_reminders_clan ON reminders(clan_tag);

-- Records that a reminder already fired for a given event, to avoid duplicates.
CREATE TABLE IF NOT EXISTS reminder_logs (
    reminder_id  TEXT NOT NULL,
    fire_key     TEXT NOT NULL,
    fired_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (reminder_id, fire_key)
);
