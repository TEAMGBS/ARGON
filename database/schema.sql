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
    war_types         TEXT[] NOT NULL DEFAULT '{}', -- subset of 'normal' | 'cwl' | 'friendly'; empty = all
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Added after the initial release; safe to re-run on an existing database.
ALTER TABLE reminders ADD COLUMN IF NOT EXISTS war_types TEXT[] NOT NULL DEFAULT '{}';

CREATE INDEX IF NOT EXISTS idx_reminders_guild ON reminders(guild_id);
CREATE INDEX IF NOT EXISTS idx_reminders_clan ON reminders(clan_tag);

-- Records that a reminder already fired for a given event, to avoid duplicates.
CREATE TABLE IF NOT EXISTS reminder_logs (
    reminder_id  TEXT NOT NULL,
    fire_key     TEXT NOT NULL,
    fired_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (reminder_id, fire_key)
);


-- ---------------------------------------------------------------------------
-- Application-emoji categories (bot-global; Discord has no native categories)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS emoji_categories (
    name        TEXT PRIMARY KEY,       -- application emoji name
    category    TEXT NOT NULL,
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


-- ---------------------------------------------------------------------------
-- War logs: per-clan channel for the attack feed and war-phase embeds
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS war_logs (
    id          TEXT,
    guild_id    BIGINT NOT NULL,
    tag         TEXT NOT NULL,
    channel_id  BIGINT NOT NULL,
    war_type    TEXT NOT NULL DEFAULT '',  -- '' = all, else 'normal' | 'cwl' | 'friendly'
    timings     INTEGER[] NOT NULL DEFAULT '{1080,720,360}',  -- minutes-left marks for the phase embed
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (guild_id, tag)
);

-- Added after the initial release; safe to re-run on an existing database.
ALTER TABLE war_logs ADD COLUMN IF NOT EXISTS war_type TEXT NOT NULL DEFAULT '';
ALTER TABLE war_logs ADD COLUMN IF NOT EXISTS timings INTEGER[] NOT NULL DEFAULT '{1080,720,360}';
ALTER TABLE war_logs ADD COLUMN IF NOT EXISTS id TEXT;
-- Backfill a short id for any rows created before the id column existed.
UPDATE war_logs SET id = upper(substr(md5(random()::text || tag), 1, 6)) WHERE id IS NULL;

CREATE INDEX IF NOT EXISTS idx_war_logs_tag ON war_logs(tag);
CREATE UNIQUE INDEX IF NOT EXISTS idx_war_logs_id ON war_logs(id);

-- Per (guild, clan, war) progress: how many attacks have been posted and which
-- phase embeds have fired, so nothing is posted twice.
CREATE TABLE IF NOT EXISTS war_log_progress (
    guild_id    BIGINT NOT NULL,
    tag         TEXT NOT NULL,
    war_key     TEXT NOT NULL,
    last_order  INTEGER NOT NULL DEFAULT 0,
    events      TEXT[] NOT NULL DEFAULT '{}',
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (guild_id, tag, war_key)
);


-- ---------------------------------------------------------------------------
-- Legend League ranked tracking
-- ---------------------------------------------------------------------------
-- Per-guild channel that receives legend attack/defense notifications.
CREATE TABLE IF NOT EXISTS ranked_settings (
    guild_id    BIGINT PRIMARY KEY,
    channel_id  BIGINT NOT NULL,
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Players a guild is tracking. The same tag can be tracked by several guilds.
CREATE TABLE IF NOT EXISTS ranked_tracked (
    guild_id    BIGINT NOT NULL,
    tag         TEXT NOT NULL,
    name        TEXT NOT NULL,
    added_by    BIGINT NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (guild_id, tag)
);

CREATE INDEX IF NOT EXISTS idx_ranked_tracked_tag ON ranked_tracked(tag);

-- Last-seen trophy count per tracked tag (the poller diffs against this). One
-- row per tag globally, shared by every guild tracking that player.
CREATE TABLE IF NOT EXISTS ranked_state (
    tag         TEXT PRIMARY KEY,
    name        TEXT,
    trophies    INTEGER NOT NULL,
    season      TEXT NOT NULL,
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Every attack/defense the poller detected (a trophy rise/fall in Legend League).
CREATE TABLE IF NOT EXISTS ranked_events (
    id             BIGSERIAL PRIMARY KEY,
    tag            TEXT NOT NULL,
    season         TEXT NOT NULL,          -- CoC season key, e.g. '2026-09'
    direction      TEXT NOT NULL,          -- 'attack' | 'defense'
    delta          INTEGER NOT NULL,       -- signed trophy change (+ attack, - defense)
    trophies_after INTEGER NOT NULL,
    occurred_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ranked_events_tag_season ON ranked_events(tag, season);
CREATE INDEX IF NOT EXISTS idx_ranked_events_occurred ON ranked_events(occurred_at);
