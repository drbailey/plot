"""SQLite schema for the event log (append-only logs table)."""

SCHEMA = """
CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    exec_number INTEGER,
    level TEXT NOT NULL,
    event TEXT NOT NULL,
    task_id INTEGER,
    message TEXT,
    details TEXT
);

CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_logs_event     ON logs(event);
"""
