# Agent Rules

All agents operating within this system must follow these rules.

---

## Configuration Variables

These variables are substituted from `config.local.yml` at runtime. Copy `config.example.yml` to `config.local.yml` and set values for your environment.

### Paths (`paths.*`)

| Variable | Key in config | Description |
|----------|--------------|-------------|
| `{python}` | `paths.python` | Absolute path to the Python interpreter |
| `{pytest}` | `paths.pytest` | Absolute path to the pytest executable |
| `{ruff}` | `paths.ruff` | Absolute path to the ruff linter |
| `{plot}` | `paths.plot` | Absolute path to the plot CLI |
| `{stories_dir}` | `paths.stories_dir` | Directory where story data is stored |
| `{workspace}` | `paths.workspace` | Root workspace directory (parent of all repos) |

### Agent Models (`agents.*`)

| Variable | Key in config | Description |
|----------|--------------|-------------|
| `{planner_model}` | `agents.roles.planner.model` | Model used for planning phases |
| `{executor_model}` | `agents.roles.executor.model` | Model used for task execution |
| `{verifier_model}` | `agents.roles.verifier.model` | Model used for verification |
| `{agent_endpoint}` | `agents.default.endpoint` | API endpoint URL; empty string uses provider default |

Per-role model settings inherit from `agents.default` and override only the fields they specify.

---

## Professional Output

- No emojis in code, commits, documentation, or communication unless explicitly requested.
- Use clear, professional language.
- Be direct and factual; avoid filler phrases.
- Match the existing style of the codebase or documentation you are working in.
- Commit messages use conventional commit format. Focus on what changed and why.

---

## Code Style

- Place all imports at the top of files. Never import inside functions, methods, or classes.
- Group imports: standard library, then third-party, then local.
- Follow existing indentation and formatting conventions in the target file.
- Before writing new files, check `pyproject.toml` for the project's `line-length` setting and conform from the start.
- When a decorator applies to a function, place it in the same file as the function definition. Post-hoc application in a separate module is a last resort.
- Before writing any utility function, constant, or base class, identify the abstraction layer it belongs to and place it there. A pure utility belongs in a shared `utils.py`; a domain model belongs at the abstraction boundary it defines.
- Dependencies point toward higher-level abstractions. Concrete modules depend on abstractions; abstractions never depend on concrete implementations. Circular imports are always forbidden.

---

## File Operations

- Read a file before editing it. Understand surrounding context before making changes.
- Use targeted edits (StrReplace/patch) when changing a section of an existing file.
- Use a full overwrite only when creating a new file or replacing the majority of its content.
- Make the smallest change necessary to accomplish the task. Do not refactor code outside the task scope.
- Only create new files when necessary. Prefer editing existing files.

---

## Safety

- Never commit files containing secrets (`.env`, credentials, API keys).
- Avoid destructive git commands (force push, hard reset) unless explicitly requested.
- Never modify git config.
- Do not delete files unless the task explicitly requires it.
- When adding dependencies, use the package manager; do not invent version numbers.

---

## Python Environment

This workspace uses the pyenv **primary** virtualenv for all Python development.

Invoke tools by absolute path from `config.local.yml`. They are not guaranteed to be on PATH.

| Variable | Example — Windows (pyenv-win) | Example — Unix (pyenv) |
|----------|------------------------------|------------------------|
| `{python}` | `C:/Users/NAME/.pyenv/pyenv-win/versions/primary/Scripts/python.exe` | `/Users/NAME/.pyenv/versions/primary/bin/python` |
| `{pytest}` | `...primary/Scripts/pytest.exe` | `...primary/bin/pytest` |
| `{ruff}` | `...primary/Scripts/ruff.exe` | `...primary/bin/ruff` |
| `{plot}` | `...primary/Scripts/plot.exe` | `...primary/bin/plot` |

On Windows, executables live under `Scripts/`. On Unix, they live under `bin/`.

Interactive activation (shell sessions only):

- **Windows:** `pyenv activate primary`
- **Unix:** `pyenv activate primary`

There is no `source .../bin/activate` on Windows.

Rules:

- Install packages into primary: `{python} -m pip install <package>`
- Do not rely on `poetry run`, bare `python`, or bare tool names on PATH.

---

## Plot CLI

Use the plot CLI for all story management operations. Key commands:

```
{plot} next <story>               Route to next action
{plot} begin <story> [repo]       Begin, revise, or approve a story
{plot} state <story>              Show current state
{plot} tasks <story>              List tasks
{plot} task <story> <task_id>     Show task details
{plot} start-task <story> <task_id>
{plot} complete-task <story> <task_id> [-m <message>]
{plot} fail-task <story> <task_id> [-m <message>]
{plot} add-task <story>
{plot} finalize <story>           Mark story complete
{plot} unblock <story> -m <summary>
{plot} replan <story>             Increment iteration, return to execution
{plot} skip-stage <story> <stage> -m <reason>
{plot} repo-config <story>        Show format/lint/test commands for repo
{plot} skills [--json]            List all known skills
{plot} context <story> <task_id>  Generate verifier context bundle
{plot} verify-submit <story> <task_id> {pass|fail} [-m <findings>]
{plot} knowledge-patterns         List knowledge patterns
{plot} knowledge-search <query> [--limit N]
{plot} knowledge-record-pattern <tag> <title> [-m <description>]
{plot} knowledge-record-decision -c <context> -d <decision> -r <rationale>
{plot} knowledge-query "<sql>"    Raw SQL query against knowledge store (debug only)
{plot} logs <story>               Show log entries
{plot} log <story> -m <message>   Add a log entry
```

All commands accept `--json` for machine-readable output.

---

## Verification Requirements

The executor that generates a task's implementation does not self-verify. The verification step is performed by a separate verifier agent.

Workflow for verification:

1. After completing implementation, run `{plot} context <story> <task_id>` to generate the context bundle. This bundle contains the task objective, success criteria, scope, and plan context.
2. Pass the context bundle to the verifier agent. The verifier receives only the context bundle — it does not receive the executor's work log or internal reasoning.
3. The verifier agent independently assesses whether the success criteria are met and calls `{plot} verify-submit <story> <task_id> pass -m "<findings>"` or `{plot} verify-submit <story> <task_id> fail -m "<findings>"`.
4. `plot verify-submit` must be called before `plot complete-task`. Calling `complete-task` without a prior verification result is a workflow violation.

Verification guidelines the verifier applies:

- Requirement coverage: does the implementation address all stated criteria?
- Edge cases: are boundary conditions and unexpected inputs handled?
- Error paths: are failures handled gracefully with appropriate messaging?
- Test completeness: are tests present and meaningful for the stated criteria?

---

## Stage Flow

Planning proceeds through a 7-stage pipeline. Each stage must be completed or explicitly skipped before moving to the next.

| Order | Stage name | Purpose |
|-------|-----------|---------|
| 1 | `goal` | Define the problem and desired outcome |
| 2 | `requirements` | Enumerate functional and non-functional requirements |
| 3 | `architecture` | Design the solution structure and component boundaries |
| 4 | `task_breakdown` | Decompose architecture into executable tasks |
| 5 | `implementation` | Execute tasks |
| 6 | `verification` | Verify implementation against requirements |
| 7 | `integration` | Validate end-to-end behavior and finalize |

When a stage is not applicable, skip it explicitly:

```
{plot} skip-stage <story> <stage> -m "<reason why stage is not applicable>"
```

Never silently omit a stage. The skip reason is recorded in the story log.

---

## Communication

### Work Logging

- Document what you attempted in the task work file.
- Be specific: list files modified, commands run, and errors encountered.
- On failure, provide an actionable recommendation for the next attempt.

### Signals

- Output the correct signal at the end of every execution phase.
- Include the task ID in success and failure signals.

### Scope Adherence

- Stay within the defined task scope.
- If you discover something out of scope, note it in the work log but do not act on it.

---

## Task Execution

### Dependencies

- Verify that task dependencies are completed before starting.
- If a dependency is missing or incomplete, output BLOCKED and stop.

### Success Criteria

- Check all success criteria before marking a task complete.
- Do not mark complete if any criterion is unverified.

### Failure Handling

- If you cannot complete a task, fail gracefully.
- Document exactly what went wrong and why.
- Provide a concrete recommendation for the next attempt.

---

## Change Proposals

- Propose changes directly. Show the specific edits, code, or modifications for review.
- Do not ask "should I proceed?" before presenting the change. Let the human review the proposal and decide.
- The review step happens after seeing the proposal, not before.

---

## Linting

Always verify linting before marking tasks complete.

### Priority order

1. **Repo-specific lint command** — check first: `{plot} repo-config <story>`
2. **Container commands** — if the repo uses containers (e.g., `make format`)
3. **Default tools** — fall back only when no repo config exists

### Default linting (no repo config)

```bash
{ruff} check <src_dir>/
{python} -m mypy <src_dir>/
```

Passing ruff does not mean the code is lint-free. Many projects require mypy type checking as well.

### Checking for repo-specific commands

```bash
{plot} repo-config <story> --json
```

If `format_cmd` or `lint_cmd` is returned, use those commands instead of the defaults.

---

## Skills

Skills extend agent capabilities with domain-specific instructions. The plot CLI discovers skills from three sources:

| Source | Location |
|--------|----------|
| `core` | Built into the plot package |
| `dependency` | Registered by installed packages |
| `user` | Declared in `config.local.yml` under `skills.user` |

List all discovered skills:

```bash
{plot} skills
{plot} skills --json
```

Register a user skill in `config.local.yml`:

```yaml
skills:
  user:
    my-skill:
      path: "/path/to/my-skill/SKILL.md"
      description: "What this skill does"
```

User skills must be declared under `skills.user.<name>`, not at the top level of `skills`.
