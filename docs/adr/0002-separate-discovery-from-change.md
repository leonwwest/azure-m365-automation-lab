# ADR 0002: Separate discovery from tenant changes

## Decision

Discovery and reporting remain read-only. Remediation output is a dry-run plan; a human reviews it
before a separately authorized change mechanism can act.

## Consequences

CI can detect governance drift without holding write permissions. Remediation takes an additional
step, but the approval, rollback and post-change evidence are explicit instead of implicit.
