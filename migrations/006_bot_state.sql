-- Migration 006: Persistent bot state (offset, etc.)
CREATE TABLE IF NOT EXISTS bot_state (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL DEFAULT ''
);
INSERT INTO bot_state (key, value) VALUES ('offset_id', '') ON CONFLICT DO NOTHING;
