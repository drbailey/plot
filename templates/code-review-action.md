# Code Review Action

On-demand code review triggered by `.continue <story> review`. Generates a per-task review file for each completed task, applying fixes directly.

Each task gets its own review document: `task-{task_id}-code_review.md`. Previous task reviews are never overwritten by later ones.

This does NOT change story phase or task state. It is a read-and-fix pass that can run at any point during execution.

---

## Rules

**Before proceeding, read and follow:** `plot/agent-rules.md`

Key variables: `{plot}`, `{python}`, `{ruff}`, `{stories_dir}`, `{workspace}`

---

## Step 1: Gather Context

```bash
{plot} state {story} --json
{plot} tasks {story} --json
```

Note the value of `current_plan` — this is `n` used in all artifact paths below.

Read every completed task's work file from `{stories_dir}/{story}/story{n}/work/`.

For each completed task, extract:
- Which files were created or modified (from the Work Log)
- What functionality was added

Read each of those files from the workspace.

---

## Step 2: Review and Fix

Read `plot/templates/code-review.md` for the document structure and review rules.

For every file created or modified by completed tasks:

### Dead Code Scan

Check for and **remove**:
- Unused imports
- Orphaned functions/methods only called from deleted or rewritten code
- Unused exports in `__init__.py` or `__all__` with no consumer
- Stale references in docs, docstrings, or configs

### Quality Scan

Check for and **fix**:
- Blanket exceptions (replace with specific types)
- Unbounded loops (add max iteration guards)
- Inconsistent error handling within a class/module
- Magic constants (extract to constants module)
- Class attributes not at top of class
- Imports not at top of file
- Shell scripts using bash-specific features unnecessarily

### Simplicity Scan

Check for and **fix**:
- Naming confusion (misleading file/variable names)
- Overly broad definitions handling cases the system never encounters
- Unnecessary indirection (wrappers with a single consumer)

---

## Step 3: Lint

```bash
{plot} repo-config {story} --json
```

Run the configured lint/format commands. If none configured:

```bash
cd {repo_path}
{ruff} check --fix {modified_paths}
{ruff} check {modified_paths}
```

Fix any remaining issues.

---

## Step 4: Generate Code Review Documents

For each completed task, create or update a **separate** review file:

```
{stories_dir}/{story}/story{n}/task-{task_id}-code_review.md
```

For example, task `1` produces `task-1-code_review.md`, task `2` produces `task-2-code_review.md`.

Each document follows the structure in `plot/templates/code-review.md` and covers only the files belonging to that task.

The document should reflect the current state of the code (after fixes applied in Steps 2-3), not the state before this review.

If a task's review file already exists, replace it with an updated version. Never overwrite another task's review file.

---

## Step 5: Signal

Output:

```
REVIEW_COMPLETE: {task_count} task(s) reviewed
- Files reviewed: {count}
- Issues fixed: {count}
- Documents: {stories_dir}/{story}/story{n}/task-{task_id}-code_review.md [...]
```

**STOP** after output.

---

## CLI Reference

```bash
{plot} state <story> [--json]
{plot} tasks <story> [--json]
{plot} repo-config <story> [--json]
{plot} log <story> <EVENT> [--task=ID] [-m M]
```
