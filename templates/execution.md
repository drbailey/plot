# Execution: Execute or Unblock a Task

Entry point when `plot next` returns ACTION: `execute_task` or `resolve_block`. One action per
invocation — do not start a second task in the same session.

---

**Before proceeding, read and follow:** `plot/agent-rules.md`

Key variables: `{plot}`, `{python}`, `{stories_dir}`

---

## Step 1: Confirm Action

Check the ACTION field from `plot next`:

| ACTION | Meaning |
|--------|---------|
| `execute_task` | Pick up the next pending task |
| `resolve_block` | A previously blocked task is being retried; read the block reason before proceeding |

If the action is anything else, this template does not apply. Check `.cursorrules` for the
correct template.

## Step 2: Read the Task Definition

The task definition is the authoritative source of truth for what to build and how to verify it.
It lives at:

```
{stories_dir}/{story}/story{n}/tasks/task-{id}-{slug}.md
```

Read it now. It contains: Objective, Success Criteria, Scope (In/Out), Approach, and Notes.

The work log — where you record your progress — is a **separate file**:

```
{stories_dir}/{story}/story{n}/work/task-{id}-work.md
```

Append all progress to the work log. Do not modify the task definition file.

## Step 3: Check Dependencies

Before starting execution:

1. Identify every task listed under **Dependencies** in the task definition.
2. Confirm each dependency has status `complete`.
3. If any dependency is incomplete or missing, go to [Blocking](#blocking) and stop.

## Step 4: Execute

Work through the Approach steps in the task definition. Apply all rules from `agent-rules.md`
for code changes, file operations, linting, and safety.

As you work, append to the work log:

- Files created or modified
- Commands run and their output
- Errors encountered and how they were resolved
- Anything out of scope that was noticed (note only; do not act on it)

### Blocking

If execution cannot proceed due to a missing external dependency, unresolvable constraint, or
missing information:

1. Append a block summary to the work log.
2. Log the block:

   ```bash
   {plot} log {story} BLOCKED --task={task_id} -m "{block reason}"
   ```

3. Output:

   ```
   BLOCKED: {reason}
   - Task: {task_id}
   - Resolution needed: {what is required to unblock}
   ```

4. Stop. Do not call `plot fail-task`.

## Step 5: Quality Gate

Before marking the task complete, run the full quality gate.

Read `templates/quality-gate.md` and work through every item. For each failure:

1. Fix the issue.
2. Record the fix in the work log.

If an item genuinely does not apply (e.g., no new behavior introduced, mypy not installed),
note the reason in the work log and continue.

## Step 6: Generate Verification Context

Quality gate must pass before this step.

```bash
{plot} context {story} {task_id}
```

This writes the verification context bundle to:

```
{stories_dir}/{story}/story{n}/verify/task-{task_id}-context.md
```

Output:

```
VERIFY_REQUIRED: context at {stories_dir}/{story}/story{n}/verify/task-{task_id}-context.md
- An independent verifier agent must assess this task before it is marked complete.
- Pass only the context file to the verifier — not this work log or your reasoning.
- Verifier calls: {plot} verify-submit {story} {task_id} <pass|fail> -m "<findings>"
```

## Step 7: Plan Evaluation

Review the remaining task list before signaling:

```bash
{plot} tasks {story}
```

If this task's work reveals that a pending task is now unnecessary, blocked, or needs scope
adjustment, record that observation in the work log as a recommendation. Do not modify task
definitions.

## Step 8: Signal

### On success

```bash
{plot} complete-task {story} {task_id} -m "{brief summary of work done}"
```

Output:

```
TASK_COMPLETE: {task_id} — {title}
- Work log: {stories_dir}/{story}/story{n}/work/task-{task_id}-work.md
- Verification context: {stories_dir}/{story}/story{n}/verify/task-{task_id}-context.md
- Remaining tasks: {n}
```

### On failure

```bash
{plot} fail-task {story} {task_id} -m "{what failed and why}"
```

Still run Step 6 before signaling failure — the verifier needs the context bundle regardless of
outcome.

Output:

```
TASK_FAILED: {task_id} — {title}
- Reason: {what failed}
- Work log: {stories_dir}/{story}/story{n}/work/task-{task_id}-work.md
- Verification context: {stories_dir}/{story}/story{n}/verify/task-{task_id}-context.md
- Recommendation: {concrete next step for the next attempt}
```

---

## CLI Reference

```bash
{plot} tasks {story}                                   # List remaining tasks
{plot} repo-config {story} [--json]                   # Show lint/format/test commands for repo
{plot} context {story} {task_id}                      # Generate verification context bundle
{plot} complete-task {story} {task_id} [-m MSG]       # Mark task complete
{plot} fail-task {story} {task_id} [-m MSG]           # Mark task failed
{plot} log {story} <EVENT> [--task=ID] [-m MSG]       # Append a log entry
```
