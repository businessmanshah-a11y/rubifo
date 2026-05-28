-- Migration 011: Create logs table for user activity and system events
-- This table was referenced in bot/handlers.py and admin/routes.py but never created.

CREATE TABLE IF NOT EXISTS logs (
    id          SERIAL PRIMARY KEY,
    level       VARCHAR(20)  NOT NULL DEFAULT 'info',
    user_id     TEXT,
    action      VARCHAR(255),
    message     TEXT,
    created_at  TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_logs_user_id    ON logs(user_id);
CREATE INDEX IF NOT EXISTS idx_logs_level      ON logs(level);
CREATE INDEX IF NOT EXISTS idx_logs_created_at ON logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_logs_action     ON logs(action);
