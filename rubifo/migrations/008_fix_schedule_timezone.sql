-- Migration 008: Fix next_run stored as Tehran time instead of UTC
-- Subtract 3:30 from all future next_run values to convert Tehran→UTC
UPDATE schedules
SET next_run = next_run - INTERVAL '3 hours 30 minutes'
WHERE next_run > NOW();
