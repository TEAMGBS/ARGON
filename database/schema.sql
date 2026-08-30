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
-- Per-user preferences (timezone)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS user_settings (
    discord_id  BIGINT PRIMARY KEY,
    timezone    TEXT,
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


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
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (guild_id, tag)
);

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
-- Clan tag aliases (short names that stand in for a tag)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS aliases (
    id          SERIAL PRIMARY KEY,
    guild_id    BIGINT NOT NULL,
    name        TEXT NOT NULL,
    tag         TEXT NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (guild_id, name)
);


-- ---------------------------------------------------------------------------
-- War reminders (fired by the background scheduler)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS reminders (
    id              SERIAL PRIMARY KEY,
    guild_id        BIGINT NOT NULL,
    channel_id      BIGINT NOT NULL,
    tag             TEXT NOT NULL,
    minutes_before  INTEGER NOT NULL,
    min_remaining   INTEGER NOT NULL DEFAULT 1,
    message         TEXT NOT NULL DEFAULT 'You still have war attacks remaining!',
    role_id         BIGINT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_reminders_guild ON reminders(guild_id);

-- Records that a reminder already fired for a given war, to avoid duplicates.
CREATE TABLE IF NOT EXISTS reminder_logs (
    reminder_id  INTEGER NOT NULL,
    fire_key     TEXT NOT NULL,
    fired_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (reminder_id, fire_key)
);


-- ---------------------------------------------------------------------------
-- Flagged players (watchlist)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS flags (
    id          SERIAL PRIMARY KEY,
    guild_id    BIGINT NOT NULL,
    tag         TEXT NOT NULL,
    name        TEXT,
    reason      TEXT NOT NULL,
    flagged_by  BIGINT NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (guild_id, tag)
);

CREATE INDEX IF NOT EXISTS idx_flags_guild ON flags(guild_id);
