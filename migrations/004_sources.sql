-- Migration 004: Source-based architecture
-- Replaces channel-based routing with user-managed content sources

-- SOURCES: collections of posts managed by users
CREATE TABLE sources (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_sources_user_id ON sources(user_id);

-- SOURCE_POSTS: individual posts belonging to a source
CREATE TABLE source_posts (
    id SERIAL PRIMARY KEY,
    source_id BIGINT NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
    order_index INTEGER NOT NULL DEFAULT 0,
    message_type VARCHAR(50) NOT NULL,  -- text|photo|video|voice|music|file|gif
    text_content TEXT,
    file_id TEXT,
    caption TEXT,
    raw_data JSONB,
    file_id_valid BOOLEAN DEFAULT true,
    added_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_source_posts_source_id ON source_posts(source_id);
CREATE INDEX idx_source_posts_order ON source_posts(source_id, order_index);

-- SCHEDULES (was missing from previous migrations)
CREATE TABLE IF NOT EXISTS schedules (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    route_id BIGINT NOT NULL REFERENCES routes(id) ON DELETE CASCADE,
    schedule_type VARCHAR(50) NOT NULL,
    interval_minutes INTEGER,
    daily_count INTEGER,
    next_run TIMESTAMP NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_schedules_route_id ON schedules(route_id);
CREATE INDEX IF NOT EXISTS idx_schedules_next_run ON schedules(next_run) WHERE is_active = true;

-- SCHEDULE_TIMES (was missing from previous migrations)
CREATE TABLE IF NOT EXISTS schedule_times (
    id SERIAL PRIMARY KEY,
    schedule_id BIGINT NOT NULL REFERENCES schedules(id) ON DELETE CASCADE,
    hour INTEGER NOT NULL,
    minute INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_schedule_times_schedule_id ON schedule_times(schedule_id);

-- FILE_ID_ERRORS: track when file_ids expire for monitoring
CREATE TABLE file_id_errors (
    id SERIAL PRIMARY KEY,
    source_post_id BIGINT NOT NULL REFERENCES source_posts(id) ON DELETE CASCADE,
    user_id BIGINT NOT NULL,
    route_id BIGINT,
    error_msg TEXT,
    occurred_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_file_id_errors_user ON file_id_errors(user_id);
CREATE INDEX idx_file_id_errors_time ON file_id_errors(occurred_at);

-- Update routes: replace source_channel_id with source_id
ALTER TABLE routes ADD COLUMN IF NOT EXISTS source_id BIGINT REFERENCES sources(id) ON DELETE SET NULL;
ALTER TABLE routes DROP COLUMN IF EXISTS source_channel_id;
ALTER TABLE routes DROP COLUMN IF EXISTS source_guid;
ALTER TABLE routes DROP COLUMN IF EXISTS target_guid;

-- Update post_queue: add source_post_id
ALTER TABLE post_queue ADD COLUMN IF NOT EXISTS source_post_id BIGINT REFERENCES source_posts(id) ON DELETE CASCADE;
