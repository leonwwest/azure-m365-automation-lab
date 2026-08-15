# Inventory schema and migration policy

The public contract is [`schemas/inventory-v1.schema.json`](../schemas/inventory-v1.schema.json).
Every inventory carries `schema_version: 1.0.0`; the CLI validates it before any audit or report
is produced and returns exit code `3` with field-level errors for incompatible documents.

## Evolution rules

- Backward-compatible additions use optional fields and keep schema version 1.
- A required field, renamed field or changed meaning requires a new versioned schema file.
- Exporters must emit the new version only after the CLI accepts both versions during migration.
- Public fixtures remain synthetic. Real exports stay under ignored `inventory/private/` and receive
  a manual privacy review before they leave the tenant boundary.

The schema describes the minimum audit input, not a Microsoft Graph response. Object IDs, UPNs,
mail addresses and credential values are intentionally outside the contract.
