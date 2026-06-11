# Knowledge Data Model

```mermaid
erDiagram
    runs {
        INTEGER id PK
        TEXT story
        INTEGER iteration
        TEXT started_at
        TEXT completed_at
        TEXT outcome
        TEXT repo_paths
    }

    patterns {
        INTEGER id PK
        INTEGER run_id FK
        TEXT tag
        TEXT title
        TEXT description
        TEXT context
        TEXT recorded_at
        INTEGER frequency
    }

    decisions {
        INTEGER id PK
        INTEGER run_id FK
        TEXT story
        TEXT context
        TEXT decision
        TEXT rationale
        TEXT recorded_at
    }

    artifacts {
        INTEGER id PK
        INTEGER run_id FK
        TEXT story
        INTEGER iteration
        TEXT artifact_type
        TEXT file_path
        TEXT description
        TEXT recorded_at
    }

    runs ||--o{ patterns  : "run_id"
    runs ||--o{ decisions : "run_id"
    runs ||--o{ artifacts : "run_id"
```

`runs` is the top-level container — one per story iteration. `patterns.frequency`
is the only column that mutates after insert: it increments when the same
`tag + title` combination is re-recorded across runs.
