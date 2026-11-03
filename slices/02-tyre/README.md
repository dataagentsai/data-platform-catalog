# Slice 2: the tyre company (Goal 1b, decision D17)

The second domain, so the framework is proved domain-free (M3: domains are data). A tyre maker's sales,
manufacturing and quality data move from six source systems through landing (push only), bronze and silver to gold
facts and certified metrics. Over fourteen simulated days the world plants eleven incidents covering every demo
story, and the platform must notice and handle each one. Spec only: the build comes in workstreams W1 to W5.

| Folder or file | Spec | What it holds |
|---|---|---|
| [contracts/](contracts/) | ODCS v3.2.0 (adopted) | 15 contracts: 9 silver (source-aligned, ADR-001) and 6 gold. All pass the published ODCS schema. |
| [manifest/datasets/](manifest/datasets/) | DPM v0.2 | 9 datasets: how each is loaded, its ingest mode, history kind, quality actions and reconciliation entries. |
| [manifest/gold/](manifest/gold/) | DPM v0.2 | 3 dimensions through the common pipeline and 3 modelled facts (OTIF, scrap, sales), each with one declared build() (ADR-003). |
| [manifest/metrics/](manifest/metrics/) | DPM v0.2 | 3 metric views with certification, synonyms and known-answer tests (ADR-022). |
| [manifest/models/](manifest/models/) | DPM v0.2 | 1 model card, the dealer demand forecast (D16, ADR-021). |
| [manifest/platform.yaml](manifest/platform.yaml) | DPM v0.2 | Business time zone, environments, default action per severity (ADR-009) and the agents enabled (ADR-023). |
| [world.yaml](world.yaml) | DWD draft | The six mock source systems, volumes, the clock with two plants, and the incident calendar. |

The same files serve every stack in [dbs/stacks/](../../dbs/stacks/) (M4): the managed free stack to build and
test, the cloud stack for the client demo. Only the binding names products.

## The sources

| System | Kind | Datasets | Arrives by |
|---|---|---|---|
| erp_db | database with a change feed | sales order lines, deliveries (push); materials (pull, full copy) | change files every 15 minutes; a full copy nightly |
| mes_db | database with a change feed | production (push); presses (pull, full copy) | change files every 15 minutes; a full copy nightly |
| lims_drop | file drop | inspection results | one file per plant per hour |
| partner_drop | file drop | dealer sell-out | one file per dealer per month |
| dealer_api | request-response interface | dealers | pages since a cursor, every 6 hours, straight to bronze |
| press_stream | event stream | press readings | one reading per press every 10 seconds |

## The incidents

| Day | Story | Incident | Must notice (DAC) | Must handle it (DPC) |
|---|---|---|---|---|
| 3 | out of order | Press readings arrive up to 90 seconds late and out of order | LATE-03 | DPC-0060 |
| 4 | deletes | Five cancelled order lines hard-deleted at the source | DEL-01 | DPC-0017, DPC-0053 |
| 5 | late data | A dealer's October sell-out file arrives four days late | LATE-01 | DPC-0080, DPC-0059, DPC-0079 |
| 6 | resend | The same file re-sent under a new name | DUP-01 | DPC-0024, DPC-0023, DPC-0038 |
| 7 | schema change | The lab system renames defect_code in one plant's files | SCH-02 | DPC-0008 |
| 8 | out of order | An old promised-date change arrives after a newer one | SCD-02 | DPC-0025, DPC-0026 |
| 9 | mass delete | The material full copy comes back 40% short | DEL-04 | DPC-0054 |
| 10 | correction | Twelve lines were always promised a day later; a backfill plan applies it | HIST-05 | DPC-0082 |
| 11 | late dimension | Orders for a new dealer arrive two days before the dealer does | LATE-02 | DPC-0046 |
| 12 | recon mismatch | The change feed silently skips seven deliveries | REC-05 | DPC-0052, DPC-0015 |
| 13 | out of order | The stream replays 45 minutes after a restart | DUP-04 | DPC-0086, DPC-0096 |

## Checks

`tests/test_tyre.py` and `tests/test_dpm_v02.py`: every contract passes ODCS, every manifest lints clean, every
gold input, dimension and metric source resolves, every incident's detector is a DAC obligation discharged by one of
its handling capabilities, all nine demo stories are covered, and no product name appears anywhere in the slice.
