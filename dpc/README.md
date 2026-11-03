# DPC, the Data Platform Catalog (v0.2, draft)

**What a data platform must have**: each stage of the spine and each cross-cutting concern as capabilities, and
the port (interface) each one is reached through. No product names. It is the data sibling of the
[AI Harness Catalog](https://github.com/dataagentsai/ai-harness-catalog) and uses the same record shapes.

- [ports.yaml](ports.yaml): the seams every product sits behind (rule R4). 44 ports, 22 of them core. Each says
  which binding layer may fill it (`binds_in`: engine, cloud or both; decision M1, ADR-014).
- [capabilities/](capabilities/): 102 capability records, one file per concern: 32 from slice 1 (`slice: 1`) and 70
  added in 0.2.0 so every concern in the client deck has one (see [../crosswalks/deck.yaml](../crosswalks/deck.yaml)).
  A capability cites the ADRs that explain it (`adr:`, see [../adr/](../adr/)).
- [../core/archetypes.yaml](../core/archetypes.yaml): the ten pipeline archetypes, PA1 to PA10.
- [../core/stages.yaml](../core/stages.yaml) and [../core/concerns.yaml](../core/concerns.yaml): shared with DAC.

## How the pieces join

A **capability** (DPC) is something that must exist, such as "every write carries a batch key". It is reached
through a **port**, such as `table_writer`, and it **discharges** obligations in DAC, such as DUP-01 "a file
delivered twice changes no total". A **binding** (DBS, [../dbs/](../dbs/)) says which product serves each port on one stack.
Each port's **invariants** name the DAC obligation they protect, so the contract tests for a port come straight
from DAC.

## Services

The spine is split into three deployable services, so a client can adopt one alone (PLAN.html).

| Service | Spine | Core ports |
|---|---|---|
| A, acquire | sources, landing, bronze, silver | mover, landing_store, source_reader, table_writer, contract_enforcer, quarantine, stage_runner, tokenizer (stream_bus later) |
| B, model | gold, semantic | model_runner (the gold harness, ADR-003), semantic_layer, product_publisher (all later) |
| C, serve | experiences | split in 0.2.0 for the deck's Out Port: experience, conversation, data_api, event_publisher, feed_writer, vector_index, feature_store, model_registry, model_server (all later) |
| platform | all | metadata_service, orchestrator, quality_runner, reconciler, lineage_emitter, telemetry, run_log, evidence, secret_store, clock, identity_provider, object_store, compute_pool, infra_provisioner (later: profiler, cost_ledger, access_control, deployer, data_catalog, audit_log, key_manager, network_boundary, agent_runtime) |

The lander (landing to bronze) is our own code, not a port (decision D11). It uses `landing_store`,
`contract_enforcer`, `tokenizer`, `table_writer`, `quarantine` and `run_log`. A pull (`source_reader`) runs the same
lander steps in-process and writes straight to bronze (D11 as amended, ADR-002).

## The capability record

Copied from AHC's capability record. `failure_mode` becomes a Problem Lab scene; `design_decisions` become a
lesson's "decide" box. One record, three uses.

```yaml
- id: DPC-0001              # permanent, four digits
  status: draft             # draft | active | deprecated
  since: 0.1.0
  level: MUST               # MUST | SHOULD | MAY, used in the requirement
  title: Every write carries a batch key
  concern: X15              # core/concerns.yaml
  stages: [bronze, silver]  # core/stages.yaml
  archetypes: [PA1, PA2, PA3, PA4]   # core/archetypes.yaml, listed explicitly
  core: true
  port: table_writer        # dpc/ports.yaml, or null when only the kernel is involved
  requirement: >-           # the normative text
    Every write MUST carry the id of the delivery and window it came from ...
  failure_mode: >-          # what goes wrong without it
    ...
  discharges: [DUP-01, DUP-02]       # DAC obligation ids
  design_decisions:         # optional: the choices a builder faces
    - key: batch_key_source
      question: Where does the batch key come from?
      tension: ...
      resolution: ...
  realization_policy: own   # own (our code) | adopt (an open format or tool behind a port) | bind (a product, per binding)
  slice: 1                  # optional: the thin slice that first needed it
  adr: [ADR-002]            # optional: the decision records that explain it (adr/)
  see_also: [DPC-0002]
```

Checked by `scripts/lint.py`: ids, vocab, ports and DAC ids resolve, the level word is used, no product names.
Coverage (every DAC obligation discharged by at least one capability) is reported now and becomes an error at
the v0.1 gate review.
