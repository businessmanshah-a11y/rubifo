-- Add source_guid and target_guid columns to cache resolved Rubika object_guids
-- (e.g. 'c0XXXX') so we don't resolve @username on every poll cycle

ALTER TABLE routes ADD COLUMN IF NOT EXISTS source_guid TEXT;
ALTER TABLE routes ADD COLUMN IF NOT EXISTS target_guid TEXT;
