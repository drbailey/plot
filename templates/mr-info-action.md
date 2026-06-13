# MR Info Action

On-demand merge request description generator triggered by `.continue <story> mr-info`. Produces a ready-to-paste MR title and description from story state, completed tasks, and git diff.

This does NOT change story phase or task state.

---

## Rules

**Before proceeding, read and follow:** `plot/agent-rules.md`

Key variables: `{plot}`, `{stories_dir}`, `{workspace}`

---

## Step 1: Gather Story Context

```bash
{plot} state {story} --json
{plot} tasks {story} --json
```

Note the value of `current_plan` — this is `n` used in all artifact paths below.

Read:
- The plan file: `{stories_dir}/{story}/story{n}/plan/plan.md`
- Every completed task's work file from `{stories_dir}/{story}/story{n}/work/`
- Any existing code review files: `{stories_dir}/{story}/story{n}/task-*-code_review.md`

Extract:
- Plan summary (what and why)
- Per-task: objective, files created/modified, key decisions from work log
- Any post-deploy steps, assumptions, or risks noted in the plan

---

## Step 2: Gather Git Context

Determine the repo path and branches:

```bash
{plot} repo-config {story} --json
```

Get the current branch and diff against the target:

```bash
cd {repo_path}
git rev-parse --abbrev-ref HEAD
git diff --stat origin/{target_branch}...HEAD
git diff origin/{target_branch}...HEAD --name-status
```

If the repo has no remote tracking or the target branch is unknown, use `develop` or `main` as the default target. Note untracked files relevant to the story.

---

## Step 3: Generate MR Description

Read `plot/templates/mr-description.md` for the output format.

Fill in every section using data from Steps 1-2:

- **Title**: Derive from story name and plan summary. Imperative mood, under 72 chars.
- **Description**: Condense the plan summary. Include architecture flow if applicable.
- **Changes**: Map completed tasks and git diff to grouped bullets. Favor what the reviewer needs to understand, not exhaustive file lists.
- **Impact / Risk**: Pull from the plan's Risks section and any issues noted in code reviews.
- **Testing**: Pull from task work logs and code review documents.
- **Type of Change**: Select based on what tasks actually delivered.
- **Checklist**: Pre-check items that are verifiably done (e.g., lint passes, self-review via quality gate).
- **Repository**: Fill in source and target branches from git context.
- **Links**: Reference plan and code review files. Include any external links from the plan (tickets, design docs).

---

## Step 4: Write Output

Write the completed MR description to:

```
{stories_dir}/{story}/story{n}/mr_description.md
```

Also output the **title** and **description body** directly so the user can copy-paste without opening the file.

---

## Step 5: Signal

Output:

```
MR_INFO_COMPLETE: mr_description.md generated
- Tasks summarized: {count}
- Files in diff: {count}
- Document: {stories_dir}/{story}/story{n}/mr_description.md
```

**STOP** after output.

---

## CLI Reference

```bash
{plot} state <story> [--json]
{plot} tasks <story> [--json]
{plot} repo-config <story> [--json]
```
