# Addon: Data Pipeline

Supplemental guidance for tasks involving data ingestion, transformation, schema changes, or output format changes. Read this file only when the addon evaluation has identified it as active.

---

## When This Addon Applies

- Data ingestion or source connector changes
- Transformation logic modifications
- Schema changes (new or modified columns, tables, or fields)
- Entity mapping changes
- File output format changes
- Database table modifications

---

## Additional Considerations

*(Expand with project-specific guidance as patterns are established.)*

### Schema Changes
- Verify migration files are generated, not hand-written.
- Confirm downstream consumers are compatible with the new schema.

### Data Contracts
- Document any changes to field names, types, or nullability.
- Note whether the change is backward-compatible.

### Testing
- Include tests for edge cases in transformation logic.
- Verify output format against expected consumer contracts.
