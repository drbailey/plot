# Merge Request Description Template

Output format for `.continue <story> mr-info`. The agent fills in each section from story/task data and git diff.

## Output Formatting

- `##` for top-level sections, `###` for area subsections under Changes by Area
- `**Files:**` with backticked paths and ` -- ` separator for change notes
- `**What:**` and `**Why:**` bold labels in each area subsection
- Omit a section entirely if it has no content — no empty headers, no "N/A"
- `---` horizontal rule between top-level `##` sections
- Use backticked identifiers for files, classes, functions — no full code blocks

## Output Sections

The MR description contains these `##` sections in order. Each bullet below describes what goes in that section.

- **Title** — Format: `[{story}] {concise summary of what this MR delivers}`. Under 72 characters, imperative mood ("Add ...", not "Added" or "Adds").
- **Ticket** — Link to the JIRA ticket if available in plan context. Format: `[TICKET-123](https://jira.example.com/browse/TICKET-123)`.
- **Description** — 2-3 sentences summarizing what the MR changes and why. Derive from the plan summary — don't rehash every task.
- **Changes by Area** — Organize changes by area/module, not by task. Infer from completed tasks and git diff. Each area gets its own `###` subsection with `**Files:**`, `**What:**`, and `**Why:**` labels.
- **Impact / Risk** — 2-4 prose bullets on user-facing effects, performance/data implications, backwards compatibility, or rollout notes. Omit if none.
- **Testing** — 2-3 prose bullets describing how this was tested — unit tests added, local testing done, CI validation. No checkboxes.
- **Type of Change** — Single line. Examples: "Bug fix", "New feature", "Refactor", "New feature + infrastructure".

## Example Output

```markdown
## Ticket

[LOTR-370](https://jira.example.com/browse/LOTR-370)

---

## Description

Makes the telephone number field optional in Surescripts organization registration. Previously phone was required for all registrations -- this allows registrations without one, omitting the CommunicationNumbers XML block entirely.

---

## Changes by Area

### Surescripts Contracts

**Files:**
- `src/orca/core/io/surescripts/contracts.py` -- Made `telephone_number` nullable, updated validator and XML generation

**What:** `AddOrganizationRequest` now accepts `telephone_number` as optional. Validator handles None/empty, XML conditionally omits the CommunicationNumbers element.

**Why:** Surescripts does not require phone for all organization types.

### Surescripts Client

**Files:**
- `src/orca/core/io/surescripts/client.py` -- Updated `add_organization` signature and docstring

**What:** Parameter changed from `str` to `str | None = None`.

### Import Ordering

**Files:**
- `src/orca/misc/data_export/tasks/export_data/runner.py` -- Moved third-party imports above local imports

**What:** Fixed import ordering to satisfy linting rules.

---

## Testing

- Existing unit and integration tests pass (665 passed, 0 failed)
- Validated XML output omits CommunicationNumbers when phone is None
- Phone validator tested for None, empty string, and short-digit rejection

---

## Type of Change

Bug fix
```
