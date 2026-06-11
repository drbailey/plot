"""SQLite schema for the cross-run knowledge store."""

SCHEMA_VERSION = 1

SCHEMA = """
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS runs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    story       TEXT NOT NULL,
    iteration   INTEGER NOT NULL,
    started_at  TEXT NOT NULL,
    completed_at TEXT,
    outcome     TEXT,
    repo_paths  TEXT
);

CREATE TABLE IF NOT EXISTS patterns (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id      INTEGER NOT NULL,
    tag         TEXT NOT NULL,
    title       TEXT NOT NULL,
    description TEXT NOT NULL,
    context     TEXT,
    recorded_at TEXT NOT NULL,
    frequency   INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS decisions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id      INTEGER NOT NULL,
    story       TEXT NOT NULL,
    context     TEXT NOT NULL,
    decision    TEXT NOT NULL,
    rationale   TEXT NOT NULL,
    recorded_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS artifacts (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id        INTEGER NOT NULL,
    story         TEXT NOT NULL,
    iteration     INTEGER NOT NULL,
    artifact_type TEXT NOT NULL,
    file_path     TEXT NOT NULL,
    description   TEXT NOT NULL,
    recorded_at   TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_patterns_tag       ON patterns(tag);
CREATE INDEX IF NOT EXISTS idx_patterns_recorded  ON patterns(recorded_at);
CREATE INDEX IF NOT EXISTS idx_decisions_story    ON decisions(story);
CREATE INDEX IF NOT EXISTS idx_decisions_recorded ON decisions(recorded_at);
CREATE INDEX IF NOT EXISTS idx_artifacts_story    ON artifacts(story);
CREATE INDEX IF NOT EXISTS idx_artifacts_recorded ON artifacts(recorded_at);
"""
