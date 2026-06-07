-- Migration 013: Add rubika_user_id column for web-first user linking
-- web users: rubika_user_id IS NULL (not yet linked to bot)
-- bot users (existing): rubika_user_id = user_id (same Rubika GUID)
-- after linking: rubika_user_id = user_id = rubika_guid

ALTER TABLE users ADD COLUMN IF NOT EXISTS rubika_user_id TEXT UNIQUE;

-- Backfill existing bot users (user_id = Rubika GUID, not web_ prefix)
UPDATE users SET rubika_user_id = user_id WHERE user_id NOT LIKE 'web_%';

CREATE INDEX IF NOT EXISTS idx_users_rubika_user_id ON users(rubika_user_id)
  WHERE rubika_user_id IS NOT NULL;
