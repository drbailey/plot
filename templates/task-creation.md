# Task Creation from Approved Plan

Translate an approved `plan.md` into task definition files, work logs, and database entries.

---

**Before proceeding, read and follow:** `plot/agent-rules.md`

Key variables: `{plot}`, `{stories_dir}`

---

## Artifact Layout

```
{stories_dir}/{story}/story{n}/
  plan/
    plan.md          ← approved plan (source of truth; read-only from here)
    pre-design.md
  tasks/
    task-{id}-{slug}.md   ← task definition (human-editable intent)
  work/
    task-{id}-work.md     ← work log (agent output)
```

`n` is `current_plan` from `plot state {story}`.

**File naming:** slug is the task title lowercased, spaces replaced with hyphens, truncated to 40 characters. Example: `task-3-story-database-module.md`.

---

## File Formats

### Task Definition (`tasks/task-{id}-{slug}.md`)

Created by `plot add-task`. Agent fills in Scope, Approach, and Notes after creation.

```markdown
# Task {id}: {title}

## Objective

{from plan.md}

## Success Criteria

{from plan.md, numbered list}

## Scope

### In Scope

{from plan.md}

### Out of Scope

{from plan.md}

## Approach

{from plan.md, numbered steps}

## Notes

{relevant context from plan assumptions, risks, or codebase context}
```

No `## Work Log` section. Work logs are kept in a separate file.

### Work Log (`work/task-{id}-work.md`)

Created by `plot add-task`. Agents append their progress here; do not pre-populate.

```markdown
# Work Log: Task {id} — {title}

Created: {ISO timestamp}

## Work Log

```

---

## Step 1: Read State and Plan

```bash
{plot} state {story}
```

Note `current_plan` — this is `n` throughout. Read the approved plan:

```
{stories_dir}/{story}/story{n}/plan/plan.md
```

Verify `**Status**: approved`. If not, output `ERROR: Plan not yet approved` and STOP.

## Step 2: Parse Tasks from Plan

Read the `## Task Breakdown` section. For each task extract:

- Task ID and title
- Objective
- Dependencies (other task IDs)
- Success Criteria
- Scope (In / Out)
- Approach steps
- Any notes from assumptions, risks, or codebase context sections

**Success criteria completeness:** If a task includes a requirements table (e.g., an endpoint
table listing input fields and output fields), the numbered success criteria must cover every
field and constraint in that table. Do not write criteria that cover only a subset of the table.
If the plan's criteria are incomplete relative to its own table, expand them when creating the
task definition file — the task file is the authoritative source for execution, and gaps here
cause executor/verifier misalignment.

## Step 3: Create Task Files

For **each** task in order:

**1. Run `plot add-task`** (creates both the task definition skeleton and the work log):

```bash
{plot} add-task {story} {task_id} "{title}" \
    --dependencies="{comma-separated task IDs, or omit if none}" \
    --objective="{objective}" \
    --success-criteria="{success criteria}"
```

**2. Edit the task definition file** to fill in the sections left blank by the CLI:

- `## Scope` → In Scope and Out of Scope lists from the plan
- `## Approach` → numbered steps from the plan
- `## Notes` → relevant context (assumptions, risks, codebase notes)

Do not touch the work log file.

## Step 4: Stage Tracking

If `plan.md` has a `## Stage Tracking` table, find every row where Status is `skipped`. For each:

```bash
{plot} skip-stage {story} {stage} -m "{skip reason from the Skip Reason column}"
```

Skip only the stages explicitly marked `skipped` in the table. Stages marked `in-scope` require no action.

## Step 5: Transition to Execution

After all tasks are created and stage skips are registered:

```bash
{plot} update {story} phase=execution last_signal=INITIALIZED
{plot} log {story} INITIALIZED --task=0 -m "Created {n} tasks from approved plan"
```

Output:

```
INITIALIZED: {n} tasks created in {story} from approved plan
- Plan file: {stories_dir}/{story}/story{n}/plan/plan.md
```

**STOP** — Human will use `.continue` to begin execution.

---

## CLI Reference

```bash
{plot} state {story} [--json]
{plot} add-task {story} {task_id} "{title}" [-d DEPS] [-o OBJECTIVE] [-s CRITERIA]
{plot} skip-stage {story} {stage} -m "{reason}"
{plot} update {story} phase=execution last_signal=INITIALIZED
{plot} log {story} INITIALIZED --task=0 -m "{message}"
{plot} tasks {story} [--json]
```
