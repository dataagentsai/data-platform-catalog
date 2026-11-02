# DBS: Data Binding Spec

For one platform, which product sits behind each port. The only file type in the catalog where a product may be
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

Checked by `scripts/lint.py` (`lint_binding`): the schema, every bound port exists in `dpc/ports.yaml`, every id
is a DAC obligation. Tests: `tests/test_dbs.py`.

The per-concern view is generated, never written by hand: `uv run scripts/coverage.py <binding>`. Example:
`slices/01-orders/COVERAGE.md`.

The same format serves every platform: Databricks first, Microsoft Fabric next. Only the binding file and the
adapters change.
