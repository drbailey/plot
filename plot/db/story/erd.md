# Story Data Model

`story.db` holds four tables across two schema files: `story/schema.py`
(state, tasks, stages) and `logger/schema.py` (logs).

```mermaid
erDiagram
    state {
        INTEGER id PK
        TEXT story
        TEXT repo_path
        TEXT stories_dir
        INTEGER current_plan
        TEXT phase
        INTEGER last_exec_number
        INTEGER max_iterations
        INTEGER max_attempts_per_task
        TEXT last_signal
        INTEGER last_task
        INTEGER current_task
        INTEGER awaiting_human
        TEXT awaiting_human_reason
        TEXT created_at
        TEXT updated_at
        INTEGER testing_available
        INTEGER readme_exists
        INTEGER changelog_exists
        TEXT user_context
        TEXT active_stages
    }

    tasks {
        INTEGER id PK
        INTEGER task_id
        INTEGER plan_number
        TEXT title
        TEXT status
        INTEGER attempts
        TEXT dependencies
        TEXT created_at
        TEXT updated_at
        TEXT objective
        TEXT success_criteria
        TEXT scope_in
        TEXT scope_out
        TEXT approach
        TEXT notes
        TEXT work_log
        TEXT verify_status
        TEXT verify_file
    }

    stages {
        INTEGER id PK
        TEXT story
        INTEGER iteration
        TEXT stage
        TEXT status
        TEXT skip_reason
        TEXT artifact_paths
        TEXT recorded_at
    }

    logs {
        INTEGER id PK
        TEXT timestamp
        INTEGER exec_number
        TEXT level
        TEXT event
        INTEGER task_id
        TEXT message
        TEXT details
    }

    state ||--o{ tasks  : "plan_number"
    state ||--o{ stages : "iteration"
    tasks ||--o{ logs   : "task_id"
```

`state` is a singleton row (`id = 1`). `tasks` has a composite unique key on
`(task_id, plan_number)` — the same logical task can exist across multiple plans.
`logs.task_id` is nullable; log entries not tied to a specific task omit it.
`dependencies` in `tasks` is stored as a JSON array of `task_id` integers.
