# Debugging story: incompatible inventory stopped before audit

## Symptom

An inventory represented `users[0].enabled` as the string `"yes"`. Earlier code would pass the
document to audit rules, where Python truthiness could make the value look enabled.

## Diagnosis and fix

The input boundary had no machine-readable contract. A Draft 2020-12 JSON Schema now validates
the whole document before audit execution and reports `users.0.enabled` as the failing path.

## Prevention

The committed fixture is validated in CI, incompatible fixtures have a regression test, and
schema evolution follows the migration policy in `docs/inventory-schema.md`.
