# Evaluate Addons

Reusable addon evaluation process. Parent templates reference this file to determine which addons apply to the current work. Inclusion criteria live here so parents do not need to maintain their own.

---

## Addon Registry

Evaluate each addon's criteria against what is known about the current work (codebase findings, plan description, user_context). **Do not read addon template files during evaluation** — only note which addons apply.

| Addon | Template | Include when |
|-------|----------|--------------|
| data-pipeline | `plot/templates/addons/data-pipeline.md` | Work involves data ingestion, transformation, database schema changes, new or modified database columns or fields, ORM/storage entity mapping changes, file output format changes, or database table modifications. Does NOT apply to API request/response model authoring (Pydantic, OpenAPI, etc.) unless those models directly mirror a storage schema change. |

---

## Evaluation Process

1. **Evaluate** each addon's "Include when" criteria against the current context.
2. **Note** which addons are active — do not read addon template files yet.
3. **Return** the list of active addons to the parent template.

The parent template is responsible for:
- **When** to read active addon templates (typically at the generation step)
- **Where** addon sections are placed in the output artifact
- **Recording** active addons in artifact metadata (e.g., the `Addons` field in `plan.md`)
