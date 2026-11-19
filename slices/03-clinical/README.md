# Slice 3: the clinical trial

The third domain, so the framework is proved domain-free a second time (M3: domains are data). A trial's subject
visits, adverse events, laboratory results, drug supply and cold chain data move from six source systems through
landing, bronze and silver to gold facts and certified metrics. The same platform that runs the tyre company runs this
one: only the manifests, contracts, world and the gold models (the business rules) differ. Over fourteen simulated days
the world plants twelve incidents covering every demo story; the platform must notice and handle each one.

| Folder or file | Spec | What it holds |
|---|---|---|
| [contracts/](contracts/) | ODCS v3.2.0 (adopted) | 16 contracts: 9 silver (source-aligned, ADR-001) and 7 gold. All pass the published ODCS schema. |
| [manifest/datasets/](manifest/datasets/) | DPM v0.2 | 9 datasets: how each is loaded, its ingest mode, history kind, quality actions and reconciliation entries. |
| [manifest/gold/](manifest/gold/) | DPM v0.2 | 3 dimensions through the common pipeline (site, subject, kit) and 4 modelled facts (visit compliance, laboratory out of range, enrolment, temperature excursions), each with one declared build() (ADR-003). |
| [manifest/metrics/](manifest/metrics/) | DPM v0.2 | 4 metric views with certification, synonyms and known-answer tests (ADR-022). |
| [manifest/platform.yaml](manifest/platform.yaml) | DPM v0.2 | Business time zone, environments, default action per severity (ADR-009) and the agents enabled (ADR-023). |
| [world.yaml](world.yaml) | DWD draft | The six mock source systems, volumes, the clock, and the incident calendar with a named `compressed` calendar. Each incident carries a `params:` block with its exact values, which the world generator reads. |

The same files serve every stack in [dbs/stacks/](../../dbs/stacks/) (M4). Only the binding names products. The gold
build models (the SQL and dataframe functions the manifests reference) live in the framework repository under
`models/clinical/`; they hold the business rule and nothing else (BLD-01).

## The sources

| System | Kind | Datasets | Arrives by |
|---|---|---|---|
| edc_db | database with a change feed | visits, adverse events (push); subjects (pull, full copy) | change files every 15 minutes; a full copy nightly |
| supply_db | database with a change feed | dispensing (push); kits (pull, full copy) | change files every 15 minutes; a full copy nightly |
| lab_drop | file drop | laboratory results | one semicolon-separated file per site per collection day |
| site_drop | file drop | site enrolment logs | one file per site per month |
| ctms_api | request-response interface | sites | pages since a cursor, every 6 hours, straight to bronze |
| coldchain_bus | event stream | temperature readings | one reading per shipment logger every 15 minutes |

The subject identifier is restricted personal data: it is tokenised before bronze, the same token in every table, and
the run's privacy scan counts values in clear in bronze and silver (it must be 0). Gold holds only the token. The
treatment arm is blinded: it stays in silver and no gold table or metric reads it.

## The incidents

Days are those of the default 14-day calendar; `--calendar compressed` moves every one to day 2 or 3 of a 3-day run.

| Day | Story | Incident | Must notice (DAC) | Must handle it (DPC) |
|---|---|---|---|---|
| 3 | out of order | Temperature readings from six loggers arrive up to 90 seconds late and out of order | LATE-03 | DPC-0060 |
| 4 | deletes | A subject withdraws consent and the record is deleted (the next full copy lacks the key) | DEL-01 | DPC-0017, DPC-0053 |
| 5 | late data | The busiest site's laboratory file for the day before arrives a day late | LATE-01 | DPC-0080, DPC-0059, DPC-0079 |
| 6 | resend | A site's enrolment log is re-sent under a new name | DUP-01 | DPC-0024, DPC-0023, DPC-0038 |
| 7 | (history) | A site is put on hold in the trial management interface | SCD-02 | DPC-0025, DPC-0026 |
| 8 | schema change | After a protocol amendment the laboratory renames range_flag in one site's file | SCH-02 | DPC-0008 |
| 8 | out of order | An old severity change for an adverse event arrives after a newer one | SCD-02 | DPC-0025, DPC-0026 |
| 9 | mass delete | The kit full copy comes back 40% short | DEL-04 | DPC-0054 |
| 10 | correction | Six visits were always planned a day later; a backfill plan applies it | HIST-05 | DPC-0082 |
| 11 | late dimension | Subjects at a new site are entered two days before the site appears in the interface | LATE-02 | DPC-0046 |
| 12 | recon mismatch | The change feed silently skips three dispensing rows | REC-05 | DPC-0052, DPC-0015 |
| 13 | out of order | The stream replays 45 minutes after a logger gateway restart | DUP-04 | DPC-0086, DPC-0096 |

Not an incident but world content the gold fact must show: on day 2 two shipments leave the 2 to 8 degree range for
about 50 minutes (never less than one reading interval). They appear once in `fact_temperature_excursion`, whatever
arrives late or twice, and in the metric view `mv_cold_chain`.

## What the world is, and is not, faithful about

See `fidelity:` in [world.yaml](world.yaml). Two choices matter for reading the numbers:

- The visit schedule is compressed (screening to week 12 in 21 days) and a visit is recorded on the day it happens, so a
  window never changes after it has been published except by an incident. Subjects were screened in the 22 days
  before the clock starts; visits before the clock are loaded on day 1 without laboratory orders.
- Subjects at the late site have no laboratory arrangement and no enrolment log until the site appears, so only the
  visit fact carries rows on the unknown member (kept inside its 3% orphan limit).

## Known answers and scale

The metric views' known answers are the seed-23 world's values after the full 14-day run at scale 1.0, from the oracle's
last day (computed from the world's own truth, without running the platform at that scale). A run at scale 0.1 holds a
tenth of the subjects, so its numbers differ; the run's console prints the spec's value beside the world's and beside
what gold says, and the three agree at every scale where the world and gold agree (gold equals the oracle).

## Spec gaps found while building the world

| Gap | What exists | What is missing | Verdict |
|---|---|---|---|
| A duplicate adverse-event delivery | DUP-01 covers a file or batch arriving twice | The local change-capture mover never delivers a change file twice, so the world has no way to plant it; DUP-03 (duplicates inside the source) is not judged by any layer's incident check | Not planted. Pursue: a mover that re-delivers a window, then a DUP-03 judge |
| A cold-chain excursion as an incident | An excursion is a business fact the gold fact counts | No DAC obligation covers a business-rule breach in a stream, so it cannot name a detector | Planted as world content, judged by the gold comparison, not as a calendar incident. Pursue: a DAC for business-rule breaches (severity decides the action, SEV-01) |
| A corrected enrolment log restating a month | The enrolment fact is built to restate (`overwrite_window`) | The world re-sends a log byte for byte (DUP-01) but never a corrected one | Not planted. Pursue after the first run on a real source |
| A lab file renamed with the same bytes | Lab batch key is `[file_name, content_checksum]` | The engine keys a batch on the content alone, so the lab's declared key is stricter than what runs; the resend incident uses the enrolment log, whose key is the content | Reconcile the lab manifest with the engine (declare `[content_checksum]` or add the name to the engine key) |
| Corrections to lab results or enrolment | `corrections: true` on `fact_enrolment` | Only visit planned dates are corrected in the world | Not planted |

## Checks

`tests/test_clinical.py`: every contract passes ODCS, every manifest lints clean, every gold input, dimension and
metric source resolves, every incident's detector is a DAC obligation discharged by one of its handling capabilities,
all nine demo stories are covered, every incident has a `params:` block, the params equal the framework's world
generator's expectations, the compressed calendar keeps every incident on day 2 or 3, and no product name appears
anywhere in the slice.
