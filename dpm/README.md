# DPM: Data Platform Manifest

One file per dataset saying how it is loaded. Pipelines are generated from it and read it only through the
metadata DB (YAML in git, then a validating loader, then the DB).

| File | What it is |
|---|---|
| `schema/dataset.schema.json` | A dataset (v0.2). Shape kept from LakeIngestionFramework's dataset YAML; the extra blocks are what DPM adds. v0.2 adds `ingest`, `history`, `quality`, `reconciliation.entries` and `load.mass_delete_max_share`. |
| `schema/gold.schema.json` | A gold table (`gold_fact` or `gold_dimension`): grain, inputs, dimensions joined as of the event, hash keys with -1/-2, window, one `build` (SQL or a pure dataframe function) for modelled facts, materialisation, corrections, completeness, checks before publish (ADR-003 to ADR-006, ADR-017, ADR-018). |
| `schema/metric.schema.json` | A metric view: dimensions and measures, each measure with additivity, time dimension, certification, synonyms and a known-answer test (ADR-022). |
| `schema/ml_model.schema.json` | A model card: purpose, owner, target, features from gold, training window, metric and threshold, monitoring, serving, limits (D16, ADR-021). |
| `schema/platform.schema.json` | One per domain: business time zone, environments, default action per quality severity (ADR-009), enabled agents and their autonomy (ADR-023). |
| `keys.yaml` | The config keys a manifest may use, copied from LakeIngestionFramework's key registry, plus keys proposed for it. Unknown keys are rejected. |

What the linter checks beyond the schema (`scripts/lint.py`, `lint_manifest`):

- every config key is registered or proposed;
- the contract version pinned equals the contract's version;
- every column the manifest names (history order, dedup keys, reconciliation measures) is a contract column;
- every archetype exists; the volume band is the right way round.

The manifest never repeats the contract: columns, types and quality rules live in the ODCS file it points to.
What `scripts/lint_shape.py` adds for v0.2 (`lint_domain`): history fits the load pattern and tracks contract
columns; pull and stream datasets have no landing hop (ADR-002); full copies detect deletes and only they carry a
mass-delete share; every severity the contract uses is critical, major or minor (ODCS's `error` and `warning` are
read as critical and minor) and has an action; reconciliation entries name contract columns and a tolerance per
measure; gold grain, window, keys and checks use contract columns, inputs and dimensions resolve, one-to-one tables
have no build and modelled facts have one, materialised views only for a single input without corrections; certified
measures have a known answer and synonyms; model features and targets resolve to gold columns.

A domain is a folder of manifests (M3): `slices/<n>-<domain>/manifest/` holds `datasets/`, `gold/`, `metrics/`,
`models/` and `platform.yaml`. Examples: `slices/01-orders/manifest/orders.yaml` (v0.1) and `slices/02-tyre/`
(every v0.2 kind). Tests: `tests/test_dpm.py` and `tests/test_dpm_v02.py`, one row per way to break it.
