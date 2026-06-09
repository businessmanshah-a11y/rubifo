-- Migration 015: App settings table for admin-configurable values

CREATE TABLE IF NOT EXISTS app_settings (
    key         TEXT PRIMARY KEY,
    value       TEXT NOT NULL,
    updated_at  TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Default trial settings
INSERT INTO app_settings (key, value) VALUES
    ('trial_duration_hours', '48'),
    ('trial_reminder_hours', '24'),
    ('plan_basic_name',      'شروع حرفه‌ای'),
    ('plan_basic_price',     '1998000'),
    ('plan_basic_routes',    '1'),
    ('plan_pro_name',        'رشد'),
    ('plan_pro_price',       '3998000'),
    ('plan_pro_routes',      '3'),
    ('plan_enterprise_name', 'مقیاس'),
    ('plan_enterprise_price','9998000'),
    ('plan_enterprise_routes','10')
ON CONFLICT (key) DO NOTHING;
