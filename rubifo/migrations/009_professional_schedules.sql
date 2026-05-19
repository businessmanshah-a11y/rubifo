-- Migration 009: Professional scheduling plans

ALTER TABLE schedules ADD COLUMN IF NOT EXISTS plan_kind VARCHAR(50);
ALTER TABLE schedules ADD COLUMN IF NOT EXISTS config JSONB DEFAULT '{}'::jsonb;
ALTER TABLE schedules ADD COLUMN IF NOT EXISTS posts_per_run INTEGER DEFAULT 1;
ALTER TABLE schedules ADD COLUMN IF NOT EXISTS loop_mode BOOLEAN DEFAULT false;
ALTER TABLE schedules ADD COLUMN IF NOT EXISTS last_run TIMESTAMP;
ALTER TABLE schedules ADD COLUMN IF NOT EXISTS ends_at TIMESTAMP;
ALTER TABLE schedules ADD COLUMN IF NOT EXISTS paused_reason TEXT;

UPDATE schedules
SET plan_kind = schedule_type
WHERE plan_kind IS NULL;

UPDATE schedules
SET config = COALESCE(config, '{}'::jsonb);

ALTER TABLE schedule_times ADD COLUMN IF NOT EXISTS scheduled_at TIMESTAMP;
ALTER TABLE schedule_times ADD COLUMN IF NOT EXISTS status VARCHAR(30) DEFAULT 'pending';
ALTER TABLE schedule_times ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}'::jsonb;

UPDATE schedule_times st
SET scheduled_at = s.next_run
FROM schedules s
WHERE st.schedule_id = s.id AND st.scheduled_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_schedules_plan_kind ON schedules(plan_kind);
CREATE INDEX IF NOT EXISTS idx_schedule_times_scheduled_at
  ON schedule_times(schedule_id, scheduled_at)
  WHERE status = 'pending';
