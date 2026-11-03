# Slice 1: orders, source to silver

The first thin slice (PLAN.html, B1). A clothing shop's orders move from its database, through landing and
bronze, to silver with history kept. Over seven simulated days the world plants four incidents, and the platform
must notice and handle each one. The slice is spec only: building it comes after the v0.1 gate review.

| File | Spec | What it holds |
|---|---|---|
| [contracts/orders.odcs.yaml](contracts/orders.odcs.yaml) | ODCS v3.2.0 (adopted) | Columns, key, grain, quality rules, freshness and retention. Passes the published ODCS schema. |
| [manifest/orders.yaml](manifest/orders.yaml) | DPM draft | How the dataset is loaded: the framework's existing dataset file plus the new blocks DPM adds. |
| [world.yaml](world.yaml) | DWD draft | The shop world: clock, change feed, population and the incident calendar. |
| [../../dbs/stacks/free-edition.yaml](../../dbs/stacks/free-edition.yaml) | DBS stack | Which product serves each port: the engine layer's free-edition profile, no cloud layer (moved there in 0.2.0, decision M1). Coverage: [free-edition.COVERAGE.md](../../dbs/stacks/free-edition.COVERAGE.md). |
| [../../dpc/capabilities/](../../dpc/capabilities/) | DPC | The 32 capabilities slice 1 needs (marked `slice: 1`). |

## The four incidents

| Day | Incident | Must notice (DAC) | Must handle it (DPC) | Judged by |
|---|---|---|---|---|
| 3 | The same delivery arrives again under a new name | DUP-01 | DPC-0024 batch key, DPC-0023 deliveries kept as received | Silver totals equal the world's truth |
| 4 | Three cancelled orders are deleted at the source | DEL-01 | DPC-0017 deletes detected and applied | The three are marked deleted, not counted as current |
| 5 | An old status change arrives after a newer one | SCD-02 | DPC-0025 history by change sequence, DPC-0026 late changes | One current row with the newest status, no overlaps |
| 6 | The source renames `amount` to `order_amount` | SCH-02 | DPC-0008 schema checked before silver | The load stops naming the column; no nulls loaded |

## What the binding says we build ourselves

On this stack, no product meets five of slice 1's obligations: a check over zero rows reports an error
(GATE-01), protected contract files (GATE-02), reconciliation that names the hop (REC-05), a configuration
fingerprint per run (CFG-03), and incidents joined to detectors (SIM-01). This list is the delta the platform
framework exists to supply.

## Checks

`tests/test_slices.py` checks that the five files agree: ids resolve, the manifest pins the contract version,
every column the manifest names is in the contract, every incident has a detector and a capability, every port
the slice uses is bound, and no product name appears outside the binding.
