# ADR 0001: Use a sanitized inventory as the tenant boundary

## Decision

Tenant Guard audits a small, versioned inventory contract instead of persisting raw Microsoft
Graph responses. The exporter requests read-only scopes and drops object IDs, addresses and
credential values before writing locally.

## Consequences

The audit is deterministic and safe to demonstrate with fictional data. Some Graph detail is not
available to rules, so a new rule must first justify and document every additional field.
