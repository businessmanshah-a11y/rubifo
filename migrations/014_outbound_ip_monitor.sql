CREATE TABLE IF NOT EXISTS outbound_ip_monitor (
    id              INTEGER PRIMARY KEY DEFAULT 1,
    current_ip      TEXT,
    previous_ip     TEXT,
    status          TEXT NOT NULL DEFAULT 'unknown',
    last_checked_at TIMESTAMP,
    last_changed_at TIMESTAMP,
    last_error      TEXT,
    alert_sent_at   TIMESTAMP,
    updated_at      TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT outbound_ip_monitor_singleton CHECK (id = 1)
);
