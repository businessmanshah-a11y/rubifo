-- Migration 005: Change user_id columns from BIGINT to TEXT
-- Rubika user/chat IDs are GUIDs (e.g. 'b0HRK4L0eQ801171186fa5bbeb370492'), not integers.
-- All tables that store the Rubika GUID directly (not users.id FK) must use TEXT.

-- 1. users.user_id: the Rubika GUID column
ALTER TABLE users ALTER COLUMN user_id TYPE TEXT;

-- 2. routes.user_id: stores Rubika GUID directly (not FK to users.id)
ALTER TABLE routes DROP CONSTRAINT IF EXISTS routes_user_id_fkey;
ALTER TABLE routes ALTER COLUMN user_id TYPE TEXT;

-- 3. subscriptions.user_id: stores Rubika GUID directly
ALTER TABLE subscriptions DROP CONSTRAINT IF EXISTS subscriptions_user_id_fkey;
ALTER TABLE subscriptions ALTER COLUMN user_id TYPE TEXT;

-- 4. transactions.user_id: stores Rubika GUID directly
ALTER TABLE transactions DROP CONSTRAINT IF EXISTS transactions_user_id_fkey;
ALTER TABLE transactions ALTER COLUMN user_id TYPE TEXT;

-- 5. schedules.user_id: stores Rubika GUID directly
ALTER TABLE schedules DROP CONSTRAINT IF EXISTS schedules_user_id_fkey;
ALTER TABLE schedules ALTER COLUMN user_id TYPE TEXT;

-- 6. file_id_errors.user_id: stores Rubika GUID directly
ALTER TABLE file_id_errors ALTER COLUMN user_id TYPE TEXT;

-- routes.target_channel_id was BIGINT NOT NULL but stores Rubika channel GUID (TEXT)
ALTER TABLE routes ALTER COLUMN target_channel_id TYPE TEXT USING target_channel_id::TEXT;

-- Drop the unique index on users.user_id and recreate (type change may need this)
DROP INDEX IF EXISTS idx_users_user_id;
CREATE UNIQUE INDEX IF NOT EXISTS idx_users_user_id ON users(user_id);
