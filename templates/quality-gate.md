# Quality Gate Checklist

**Before proceeding, read and follow:** `plot/agent-rules.md`

Work through every item before marking a task complete. For each item: check it off if it passes,
or note the reason it does not apply.

---

## 1. Linting

### 1a. Check for repo-specific lint command (check first)

```bash
{plot} repo-config {story} --json
```

If `lint_cmd` is returned, run it. If it passes, items 1b and 1c are satisfied.

### 1b. Ruff (default when no repo lint_cmd)

```bash
{ruff} check {src_dir}/
```

All errors must be resolved. Warnings may be noted in the work log but do not block.

Ruff enforces line length, import ordering, and common style rules automatically. Additionally
verify by inspection: no imports appear inside functions, methods, or classes.

### 1c. Mypy (if installed)

```bash
{python} -m mypy {src_dir}/
```

Run only if mypy is available in the virtualenv. All errors must be resolved before proceeding.

If mypy is not installed, note "mypy not present" in the work log and continue.

---

## 2. No Hardcoded Paths

- [ ] All file paths are constructed from config variables (`{stories_dir}`, `{workspace}`,
  `{python}`, `{plot}`, etc.) or derived from runtime values.
- [ ] No absolute paths are embedded in source files (e.g. `/Users/name/`, `C:\Users\name\`).
- [ ] No home-directory shorthand (`~`) is hardcoded in source or template files.

---

## 3. No Secrets

- [ ] No API keys, passwords, tokens, or credentials appear in source files or templates.
- [ ] No `.env` files, credential files, or files containing secrets are staged for commit.
- [ ] Any config file that may contain sensitive values is listed in `.gitignore`.

---

## 4. Test Coverage of New Behavior

- [ ] Every new function, class, or CLI command with non-trivial logic has at least one
  corresponding test.
- [ ] Tests cover at least one success path and one failure or edge-case path.
- [ ] If no new behavior was introduced (documentation-only, config-only, or template task),
  note "no new behavior" in the work log and continue.

Check for repo-specific test command:

```bash
{plot} repo-config {story} --json
```

If `test_cmd` is returned, run it. Otherwise:

```bash
{pytest} {test_dir}/
```

All tests must pass before proceeding.

---

## Sign-Off

Record the quality gate result in the work log before proceeding to Step 6 (verification
context) in `execution.md`:

```
Quality gate: PASS
- Linting: {ruff passed | repo lint_cmd passed}
- Mypy: {passed | not present}
- No hardcoded paths: confirmed
- No secrets: confirmed
- Tests: {passed — n tests | no new behavior}
```

On failure, record what failed and what action was taken before retrying:

```
Quality gate: FAIL
- {item}: {reason}
- Action: {fix applied or explanation of why it cannot be fixed now}
```
