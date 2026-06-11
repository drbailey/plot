"""SQLite schema for story workflow: state, tasks, and stages."""

SCHEMA_VERSION = 1

SCHEMA = """
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS state (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    story TEXT NOT NULL,
    repo_path TEXT NOT NULL,
    stories_dir TEXT NOT NULL,
    current_plan INTEGER DEFAULT 0,
    phase TEXT DEFAULT 'init',
    last_exec_number INTEGER DEFAULT 0,
    max_iterations INTEGER DEFAULT 20,
    max_attempts_per_task INTEGER DEFAULT 3,
    last_signal TEXT DEFAULT 'INITIALIZED',
    last_task INTEGER,
    current_task INTEGER,
    awaiting_human INTEGER DEFAULT 0,
    awaiting_human_reason TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    testing_available INTEGER,
    readme_exists INTEGER,
    changelog_exists INTEGER,
    user_context TEXT,
    active_stages TEXT
);

CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,
    plan_number INTEGER DEFAULT 0,
    title TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    attempts INTEGER DEFAULT 0,
    dependencies TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    objective TEXT,
    success_criteria TEXT,
    scope_in TEXT,
    scope_out TEXT,
    approach TEXT,
    notes TEXT,
    work_log TEXT,
    verify_status TEXT,
    verify_file TEXT,
    UNIQUE(task_id, plan_number)
);

CREATE TABLE IF NOT EXISTS stages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    story TEXT NOT NULL,
    iteration INTEGER NOT NULL,
    stage TEXT NOT NULL,
    status TEXT NOT NULL,
    skip_reason TEXT,
    artifact_paths TEXT,
    recorded_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_tasks_plan    ON tasks(plan_number);
CREATE INDEX IF NOT EXISTS idx_tasks_status  ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_stages_lookup ON stages(story, iteration, stage);
"""
