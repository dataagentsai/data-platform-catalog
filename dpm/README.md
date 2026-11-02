# DPM: Data Platform Manifest

One file per dataset saying how it is loaded. Pipelines are generated from it and read it only through the
metadata DB (YAML in git, then a validating loader, then the DB).

| File | What it is |
|---|---|
| `schema/dataset.schema.json` | The manifest's JSON schema (v0.1). Shape kept from LakeIngestionFramework's dataset YAML; the extra blocks are what DPM adds. |
| `keys.yaml` | The config keys a manifest may use, copied from LakeIngestionFramework's key registry, plus keys proposed for it. Unknown keys are rejected. |

What the linter checks beyond the schema (`scripts/lint.py`, `lint_manifest`):

- every config key is registered or proposed;
- the contract version pinned equals the contract's version;
- every column the manifest names (history order, dedup keys, reconciliation measures) is a contract column;
- every archetype exists; the volume band is the right way round.

The manifest never repeats the contract: columns, types and quality rules live in the ODCS file it points to.
Example: `slices/01-orders/manifest/orders.yaml`. Tests: `tests/test_dpm.py`, one row per way to break it.
