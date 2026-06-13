# Finalization: Complete Task Family

All tasks are complete. Lint, test, update documentation, record knowledge, and finalize the
story.

---

**Before proceeding, read and follow:** `plot/agent-rules.md`

Key variables: `{plot}`, `{python}`, `{pytest}`, `{ruff}`, `{stories_dir}`, `{max_test_iterations}`

---

## Iteration Loop

Steps marked **"apply the iteration loop"** follow this pattern:

1. Run the command.
2. **If PASS:** continue to the next step.
3. **If FAIL:** analyze the output, apply a fix, and re-run.
4. After `{max_test_iterations}` total attempts without passing, log a block and stop:

```bash
{plot} log {story} BLOCKED --task={task_id} -m "<step> failing after {max_test_iterations} iterations: <summary>"
```

---

## Part 1: Gather Context

```bash
{plot} state {story}
```

Note the value of `current_plan` — this is `n` used in all artifact paths below.

```bash
{plot} tasks {story}
```

Read every `task-*.md` file in `{stories_dir}/{story}/story{n}/tasks/`. For each completed task,
extract: what was implemented, which files changed, what functionality was added. This context
informs the E2E test script and documentation steps.

---

## Part 2: Lint

### Step 2.1: Determine Commands

```bash
{plot} repo-config {story}
```

Note the returned `format_cmd`, `lint_cmd`, and `test_cmd` — used throughout Parts 2 and 3.

### Step 2.2: Run Lint

If `format_cmd` or `lint_cmd` was returned in Step 2.1, use those. Otherwise:

```bash
cd {repo_path}
{ruff} check --fix src/
{ruff} check src/
```

### Step 2.3: Fix and Repeat

Let auto-fix handle what it can. Manually fix the remainder. Apply the iteration loop.

---

## Part 3: Test

### Step 3.1: Create Debugging Directory

```bash
mkdir {stories_dir}/{story}/story{n}/debugging/
```

### Step 3.2: Run Existing Tests

Use `test_cmd` from Step 2.1 if available. Otherwise use the test runner detected by the scanner
(`test_framework` in the `plot state` scan output) with its standard invocation:

```bash
cd {repo_path}
{pytest} -v tests/       # pytest (default)
# npx jest               # jest
# npx vitest run         # vitest
```

Apply the iteration loop.

### Step 3.3: E2E Testing

Create `{stories_dir}/{story}/story{n}/debugging/test_e2e.sh` (or `.py`) that exercises the
built functionality end-to-end. Run it.

On pass, continue to Step 3.4. On fail:
- **Small fix** (bug, typo, off-by-one): apply the iteration loop.
- **Broad changes** (architecture wrong, multiple unrelated files, new dependencies needed):
  trigger REPLAN — see Part 5.

### Step 3.4: Add New Unit Tests

For new functionality:
1. Follow existing test patterns in the repo.
2. Create tests for new public APIs and functions.
3. Create regression tests for bugs found during E2E.

### Step 3.5: Run New Unit Tests

Use the same test runner as Step 3.2, scoped to the new test files. Apply the iteration loop.

### Step 3.6: Re-lint After New Tests

New test files must also pass lint. Re-run the lint command from Step 2.2. Apply the iteration
loop.

### Step 3.7: Document Test Results

Create `{stories_dir}/{story}/story{n}/debugging/test-results.md` with: test environment,
commands run, results, bugs found, and new tests added.

---

## Part 4: Documentation

**Only proceed after tests and linting pass.**

### Step 4.1: Update README

**Skip if `readme_exists: false` in `plot state` output.** Add minimal docs for user-facing
changes. Match existing style.

### Step 4.2: Update CHANGELOG

**Skip if `changelog_exists: false` in `plot state` output.** Add entries under the Unreleased
section.

### Step 4.3: Create Code Review

Create `{stories_dir}/{story}/story{n}/code_review.md` covering:
- Summary of changes made
- Files added, modified, or deleted
- Key design decisions and trade-offs
- Any risks or follow-up items

### Step 4.4: Create Summary

Create `{stories_dir}/{story}/story{n}/summary.md` with: what was built, tasks completed,
testing status, docs updated, and recommended next steps.

---

## Part 5: Replan (Only If Broad Changes Needed)

**Only trigger if E2E reveals issues requiring broad changes to the implementation.**

Signs a replan is needed:
- Fix requires changes to multiple unrelated files
- A core assumption in the plan was wrong
- New external dependencies are required
- The architecture must be restructured

Signs a replan is **not** needed (fix directly):
- A single function or module has a bug
- A test assertion is wrong
- A missing nil/null check
- A minor logic error in one location

```bash
{plot} replan {story} -m "{reason}"
```

Output: `REPLAN: story{n} -> story{n+1}`

**STOP** — `.continue` will route back to execution.

---

## Part 6: Knowledge Recording

**Required step before finalizing.** Record patterns and decisions from this story so future
stories benefit.

### Step 6.1: Record Implementation Patterns

For each significant implementation decision or recurring pattern identified during this story,
record one entry:

```bash
{plot} knowledge-record-pattern <tag> "<title>" -m "<description of the pattern>"
```

Record at least one pattern per significant implementation decision.

### Step 6.2: Record Architectural Decisions

For each architectural choice made during this story:

```bash
{plot} knowledge-record-decision -c "<context: what situation prompted this decision>" \
    -d "<decision: what was chosen>" \
    -r "<rationale: why this choice was made>"
```

Record one decision entry per architectural choice.

---

## Part 7: Complete

```bash
{plot} finalize {story} -m "All tests pass, docs updated"
```

Output:

```
FAMILY_COMPLETE: {story} (story{n})
- Tasks: {n_tasks} completed
- Tests: PASSED
- Docs: {updated/skipped}
```

**STOP** — Story is complete.

---

## CLI Reference

```bash
{plot} state <story> [--json]
{plot} tasks <story> [--json]
{plot} repo-config <story> [--json]
{plot} knowledge-record-pattern <tag> "<title>" [-m "<description>"]
{plot} knowledge-record-decision -c "<context>" -d "<decision>" -r "<rationale>"
{plot} knowledge-patterns
{plot} finalize <story> [-m M]
{plot} replan <story> [-m M]
{plot} log <story> <EVENT> [--task=ID] [-m M]
```
