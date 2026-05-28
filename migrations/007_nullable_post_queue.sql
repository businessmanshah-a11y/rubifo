-- Migration 007: Make legacy columns nullable in post_queue
-- message_id_in_source and source_date are from old architecture and not used
ALTER TABLE post_queue ALTER COLUMN message_id_in_source DROP NOT NULL;
ALTER TABLE post_queue ALTER COLUMN source_date DROP NOT NULL;
