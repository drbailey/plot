# Code Review Document Template

This template defines the structure for a **code review document** generated during story finalization. It captures what changed, how it was tested, and what reviewers should pay attention to.

---

## When to Generate

Create `{stories_dir}/{story}/story{n}/code_review.md` during Part 4 of finalization, after all tests and linting pass.

## How to Generate

Review every completed task work file and the actual code changes. The document should give a reviewer enough context to evaluate the changes without reading every task file.

Rules:
- Organize changes by area/module, not by task number
- Be specific about files — list every file touched
- Flag anything that warrants extra scrutiny
- Note any deviations from the original plan
- Keep it factual; skip filler
- **Remove** dead code and unnecessary complexity during the review — don't just flag it
- This code will be read by humans; favor simple, clean, obvious code

---

## Document Structure

```markdown
# Code Review: {story} - Story {n}

> **Date**: {timestamp}
> **Repository**: {repo_path}
> **Tasks completed**: {count}

## Overview

{2-3 sentences. What was the goal? What was delivered?}

## Changes by Area

### {Area/Module 1}

**Files:**
- `path/to/file.py` -- {what changed}
- `path/to/other.py` -- {what changed}

**What:** {1-2 sentences on what this area's changes accomplish}

**Why:** {rationale if not obvious from the plan}

---

### {Area/Module 2}

(same structure)

---

## New Dependencies

| Package | Version | Why |
|---------|---------|-----|
| {pkg} | {ver} | {reason} |

(Remove this section if none)

## Database / Schema Changes

{Describe any migrations, schema changes, or data model updates.}

(Remove this section if none)

## Test Coverage

| Category | Result | Notes |
|----------|--------|-------|
| Existing tests | PASSED | {any fixes needed?} |
| E2E tests | PASSED | {iterations needed, bugs found} |
| New unit tests | {count} added | {what they cover} |
| Regression tests | {count} added | {bugs they prevent} |

## Bugs Found During Testing

| Bug | How Found | Fix | Regression Test |
|-----|-----------|-----|-----------------|
| {description} | {E2E / unit test / manual} | {what was fixed} | {test name or N/A} |

(Remove this section if none)

## Plan Deviations

{List any changes made that differ from the original plan.md -- tasks skipped, scope adjusted, approach changed, tasks added.}

(Remove this section if none)

## Dead Code & Simplicity Check

{Scan every new and modified file. Dead code and unnecessary complexity should be
removed during review, not deferred. Code is read by humans -- favor simple and clean.}

### Dead Code Scan

Check for and **remove**:
- **Unused imports:** imports no longer referenced in modified files
- **Orphaned functions/methods:** only called from deleted or rewritten code
- **Unused exports:** symbols exported in `__init__.py` or `__all__` with no external consumer
- **Unused fixtures/helpers:** test fixtures, factory functions, or setup code that no test uses
- **Dead scaffolding:** code that technically runs but always short-circuits
- **Stale references:** docs, docstrings, or configs that reference deleted files or renamed symbols

### Simplicity & Naming Scan

Check for and **fix**:
- **Naming confusion:** file/directory names that mislead
- **Overly broad definitions:** constants, patterns, or helpers that handle cases the system never encounters
- **Import hygiene:** imports inside functions/methods (move to top of file)
- **Unnecessary indirection:** wrappers, re-exports, or abstractions with a single consumer

| File | Issue | Action taken |
|------|-------|--------------|
| {file} | {what and why} | {removed / simplified / N/A with rationale} |

(Remove this section if nothing found)

### Unresolved In-Code Questions

Search all new and modified source files for `TODO`, `FIXME`, `HACK`, `XXX`, `QA:`, or
similar markers. Each one must be resolved before merge — either do the work, remove
the marker with a rationale, or move it to a tracked issue.

| File:Line | Marker | Resolution |
|-----------|--------|------------|
| {file}:{line} | {marker text} | {resolved / deferred to issue #N / removed with rationale} |

(Remove this section if none found)

### Side Effects & Mutation Scan

Check every new and modified function for these patterns and **fix or flag**:

- **Input mutation instead of return:** functions that modify an input parameter to produce a side effect instead of returning an explicit, self-contained result.
- **Module-level side effects:** code that runs at import time with observable consequences — config instantiation, DB connections, env var reads that throw, global registrations. Prefer lazy initialization.
- **Mutation-at-a-distance:** mutating an object that was passed in from a caller or shared across scopes.
- **Loose type annotations:** `Any` on a parameter whose concrete type is known. Use the real type or a structural protocol.

| File:Line | Pattern | Action taken |
|-----------|---------|--------------|
| {file}:{line} | {pattern description} | {fixed / flagged / N/A with rationale} |

(Remove this section if nothing found)

### Consistency Scan

Check for inconsistent patterns across files that serve the same role:

- **Architectural inconsistency:** similar code paths using different mechanisms.
- **API surface inconsistency:** trailing slashes on some routes but not others, mixed sync/async for equivalent handlers.
- **Test fixture drift:** duplicate factory functions or mock builders across test files with slightly different default values.
- **Dependency version skew:** pinned version ranges inconsistent across sibling repos.

| File(s) | Inconsistency | Action taken |
|---------|---------------|--------------|
| {files} | {what differs and why it matters} | {fixed / flagged / N/A with rationale} |

(Remove this section if nothing found)

## Potential Concerns

{Areas that deserve extra reviewer attention. Categorize by severity.}

### Must Fix (blocks merge)

- {concern and why it matters}

### Should Fix (not blocking, but creates risk)

- {concern and why it matters}

### Nice to Have (improvements for a follow-up)

- {concern and why it matters}

(Remove empty severity levels)

## Files Changed

{Complete alphabetical list of every file created, modified, or deleted.}

**Created:**
- `path/to/new_file.py`

**Modified:**
- `path/to/existing_file.py`

**Deleted:**
- `path/to/removed_file.py`
```

---

## Style Guide

- **Tone:** Factual, direct, no filler
- **Audience:** A reviewer who knows the codebase but hasn't read the task files
- **Length:** Proportional to the change — small stories get 1 page, large ones get 3-4
- **Specificity:** Always name concrete files and functions, not vague areas
