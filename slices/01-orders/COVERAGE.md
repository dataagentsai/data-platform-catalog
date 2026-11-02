# Coverage by concern: shop orders, slice 1 on Databricks Free Edition (serverless, one workspace)

Generated from `binding-databricks.yaml` by `scripts/coverage.py`; do not edit by hand.

| Concern | Port | Coverage | Gap filled by |
|---|---|---|---|
| X1 Metadata and control plane | metadata_service | platform has nothing | in-house |
| X2 Orchestration | orchestrator | platform covers it | - |
| X3 Contracts and schema evolution | table_writer | platform covers part | in-house |
| X3 Contracts and schema evolution | contract_enforcer | platform has nothing | in-house |
| X3 Contracts and schema evolution | product_publisher | not bound in this slice | - |
| X4 Data quality | contract_enforcer | platform has nothing | in-house |
| X4 Data quality | quarantine | platform covers part | in-house |
| X4 Data quality | quality_runner | platform covers part | in-house |
| X4 Data quality | evidence | platform has nothing | in-house |
| X5 Profiling | profiler | not bound in this slice | - |
| X6 Reconciliation | reconciler | platform has nothing | in-house |
| X6 Reconciliation | evidence | platform has nothing | in-house |
| X7 Lineage | lineage_emitter | platform covers it | - |
| X7 Lineage | evidence | platform has nothing | in-house |
| X8 Observability | mover | platform covers it | - |
| X8 Observability | telemetry | platform covers part | in-house |
| X9 Freshness and SLOs | experience | not bound in this slice | - |
| X9 Freshness and SLOs | telemetry | platform covers part | in-house |
| X10 Cost and FinOps | cost_ledger | not bound in this slice | - |
| X11 Security and access | experience | not bound in this slice | - |
| X11 Security and access | access_control | not bound in this slice | - |
| X11 Security and access | secret_store | platform covers it | - |
| X12 Privacy and personal data | access_control | not bound in this slice | - |
| X13 Governance, catalog and semantics | semantic_layer | platform covers it | - |
| X13 Governance, catalog and semantics | product_publisher | not bound in this slice | - |
| X14 Audit and run log | landing_store | platform covers it | - |
| X14 Audit and run log | run_log | platform has nothing | in-house |
| X14 Audit and run log | evidence | platform has nothing | in-house |
| X15 Replay, backfill and idempotency | mover | platform covers it | - |
| X15 Replay, backfill and idempotency | table_writer | platform covers part | in-house |
| X15 Replay, backfill and idempotency | model_runner | not bound in this slice | - |
| X15 Replay, backfill and idempotency | clock | platform has nothing | in-house |
| X16 Environments, CI/CD and release | deployer | not bound in this slice | - |
| X17 Testing | model_runner | not bound in this slice | - |
| X18 Resilience and recovery | landing_store | platform covers it | - |
| X19 Performance | (no port yet) | not bound in this slice | - |
| X20 Self-healing | (no port yet) | not bound in this slice | - |
| X21 Agent assistance | (no port yet) | not bound in this slice | - |
| X22 Simulation | clock | platform has nothing | in-house |

Ports bound: 16. The platform covers 6 fully, 4 in part and 6 not at all; every gap names who fills it.
