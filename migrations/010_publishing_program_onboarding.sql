-- Publishing-program onboarding: persistent destinations, wizard drafts, and purpose tags.

CREATE TABLE IF NOT EXISTS destination_channels (
    id SERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    channel_id TEXT NOT NULL,
    title TEXT,
    verification_status VARCHAR(30) NOT NULL DEFAULT 'pending',
    verification_error TEXT,
    verified_at TIMESTAMP,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_destination_channels_active
    ON destination_channels(user_id, channel_id) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_destination_channels_user
    ON destination_channels(user_id) WHERE is_active = true;

CREATE TABLE IF NOT EXISTS publishing_drafts (
    id SERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    flow_kind VARCHAR(20) NOT NULL CHECK (flow_kind IN ('tutorial', 'real')),
    step VARCHAR(80) NOT NULL,
    destination_id BIGINT REFERENCES destination_channels(id) ON DELETE SET NULL,
    source_id BIGINT REFERENCES sources(id) ON DELETE SET NULL,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_publishing_drafts_active
    ON publishing_drafts(user_id) WHERE is_active = true;

ALTER TABLE sources ADD COLUMN IF NOT EXISTS program_purpose VARCHAR(30) NOT NULL DEFAULT 'real';
ALTER TABLE routes ADD COLUMN IF NOT EXISTS destination_id BIGINT REFERENCES destination_channels(id) ON DELETE SET NULL;
ALTER TABLE routes ADD COLUMN IF NOT EXISTS program_purpose VARCHAR(30) NOT NULL DEFAULT 'real';
ALTER TABLE schedules ADD COLUMN IF NOT EXISTS program_purpose VARCHAR(30) NOT NULL DEFAULT 'real';
ALTER TABLE schedules ALTER COLUMN next_run DROP NOT NULL;

CREATE INDEX IF NOT EXISTS idx_routes_destination ON routes(destination_id);
CREATE INDEX IF NOT EXISTS idx_schedules_program_purpose ON schedules(program_purpose);

-- There are no live customers to migrate for this UX release.
TRUNCATE TABLE transactions, subscriptions, publishing_drafts, post_queue,
    schedule_times, schedules, routes, source_posts, sources, destination_channels,
    users RESTART IDENTITY CASCADE;
