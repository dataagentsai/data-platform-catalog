# DBS: Data Binding Spec

For one stack, which product sits behind each port. The only file type in the catalog where a product may be
named.

**Reused, not invented.** The format is the AI family's harness profile (`ai-harness-catalog`,
`schema/profile.schema.json`, `docs/PROFILE.md`) with the same blocks: `subject`, `catalog` (pinned versions),
`decisions` (each with its `source`: chosen, golden-path, inherited or locked), `thresholds`, `bindings`,
`accepted_gaps`. Ids point at DAC obligations instead of AHC capabilities.

**What DBS adds**, on every binding, because of the binding rule (reuse the platform, fill only the gap, drive it
from metadata, keep it behind a port, connect the dots):

| Field | Meaning |
|---|---|
| `coverage` | How much of the port the platform's own offering covers: `full`, `partial` or `none` |
| `gap` | What the offering leaves undone. Required unless coverage is full |
| `gap_filled_by` | Who fills it: `open-source` (named) or `in-house`. Required unless coverage is full |
| `metadata_keys` | Manifest fields or config keys that switch and configure the port |
| `proves` | DAC obligations this binding is tested against |

## Two layers: engine plus cloud (decision M1, ADR-014)

A platform is an **engine** (where tables, pipelines and queries run) on a **cloud** (storage, movers, streams,
identity, keys, network, infrastructure). Each half is written once; a **stack** composes them.

| Folder | What it holds | Today |
|---|---|---|
| `engine/` | One file per engine: the ports it binds, plus **profiles** for variants of the same offering | `databricks.yaml`, with the `free-edition` profile (slice 1's binding moved here) |
| `cloud/` | One file per cloud: the ports a cloud provides | `aws.yaml` |
| `stacks/` | One file per combination: engine + profile + cloud, and `prefer` for every port both layers bind | `aws-databricks.yaml` (Goal 1b), `free-edition.yaml` (slice 1, no cloud layer) |
| `schema/` | `binding.schema.json` (the composed binding, v0.1 shape), `layer.schema.json`, `stack.schema.json` | |

Each port in `dpc/ports.yaml` says which layer may fill it (`binds_in`). The linter rejects an engine file that binds
a cloud-only port (object storage, keys, network, events) and the reverse, so engine files never name a cloud
service and cloud files never name an engine feature. A new cloud is one cloud file plus adapters; a new engine is
one engine file plus adapters; the manifests do not change (M4).

Checked by `scripts/lint_shape.py` (`lint_dbs`): each layer and stack against its schema, every bound port exists
and allows that layer, profiles only unbind what the base binds, every double binding is resolved by `prefer` and
nothing else is, and the composed binding passes `binding.schema.json` and `lint_binding`. Tests:
`tests/test_dbs.py` (the composed free-edition binding) and `tests/test_dbs_layers.py`.

The per-concern view is generated per stack, never written by hand: `uv run scripts/coverage.py` writes
`stacks/<name>.COVERAGE.md`, with the layer that fills each port.
