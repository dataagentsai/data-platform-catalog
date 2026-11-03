# Coverage by concern: Databricks on AWS (dev and prod as separate catalogs, buckets, metadata schemas and bundle targets)

Stack `aws-databricks`: engine databricks + cloud aws. Generated from `dbs/stacks/aws-databricks.yaml` by `scripts/coverage.py`; do not edit by hand.

| Concern | Port | Layer | Coverage | Gap filled by |
|---|---|---|---|---|
| X1 Metadata and control plane | metadata_service | cloud | platform covers part | in-house |
| X1 Metadata and control plane | stage_runner | engine | platform covers part | in-house |
| X2 Orchestration | orchestrator | engine | platform covers it | - |
| X3 Contracts and schema evolution | table_writer | engine | platform covers part | in-house |
| X3 Contracts and schema evolution | contract_enforcer | engine | platform has nothing | in-house |
| X3 Contracts and schema evolution | product_publisher | engine | platform covers part | in-house |
| X3 Contracts and schema evolution | source_reader | engine | platform has nothing | in-house |
| X3 Contracts and schema evolution | data_api | engine | platform covers part | in-house |
| X3 Contracts and schema evolution | event_publisher | cloud | platform covers part | in-house |
| X4 Data quality | contract_enforcer | engine | platform has nothing | in-house |
| X4 Data quality | quarantine | engine | platform covers part | in-house |
| X4 Data quality | quality_runner | engine | platform covers part | in-house |
| X4 Data quality | evidence | engine | platform has nothing | in-house |
| X4 Data quality | stage_runner | engine | platform covers part | in-house |
| X4 Data quality | feature_store | engine | platform covers it | - |
| X5 Profiling | profiler | engine | platform covers part | in-house |
| X6 Reconciliation | reconciler | engine | platform has nothing | in-house |
| X6 Reconciliation | evidence | engine | platform has nothing | in-house |
| X7 Lineage | lineage_emitter | engine | platform covers it | - |
| X7 Lineage | evidence | engine | platform has nothing | in-house |
| X7 Lineage | feed_writer | engine | platform covers part | in-house |
| X7 Lineage | feature_store | engine | platform covers it | - |
| X8 Observability | mover | cloud | platform covers part | in-house |
| X8 Observability | telemetry | engine | platform covers part | in-house |
| X9 Freshness and SLOs | experience | engine | platform covers it | - |
| X9 Freshness and SLOs | telemetry | engine | platform covers part | in-house |
| X9 Freshness and SLOs | stream_bus | cloud | platform covers it | - |
| X9 Freshness and SLOs | model_server | engine | platform covers it | - |
| X10 Cost and FinOps | cost_ledger | engine | platform covers part | in-house |
| X10 Cost and FinOps | compute_pool | engine | platform covers it | - |
| X11 Security and access | experience | engine | platform covers it | - |
| X11 Security and access | access_control | engine | platform covers part | in-house |
| X11 Security and access | secret_store | cloud | platform covers it | - |
| X11 Security and access | conversation | engine | platform covers it | - |
| X11 Security and access | data_api | engine | platform covers part | in-house |
| X11 Security and access | vector_index | engine | platform covers it | - |
| X11 Security and access | model_server | engine | platform covers it | - |
| X11 Security and access | key_manager | cloud | platform covers it | - |
| X11 Security and access | identity_provider | cloud | platform covers it | - |
| X11 Security and access | network_boundary | cloud | platform covers it | - |
| X12 Privacy and personal data | access_control | engine | platform covers part | in-house |
| X12 Privacy and personal data | tokenizer | cloud | platform covers part | in-house |
| X12 Privacy and personal data | vector_index | engine | platform covers it | - |
| X12 Privacy and personal data | data_catalog | engine | platform covers part | in-house |
| X13 Governance, catalog and semantics | semantic_layer | engine | platform covers it | - |
| X13 Governance, catalog and semantics | product_publisher | engine | platform covers part | in-house |
| X13 Governance, catalog and semantics | conversation | engine | platform covers it | - |
| X13 Governance, catalog and semantics | data_catalog | engine | platform covers part | in-house |
| X14 Audit and run log | landing_store | cloud | platform covers it | - |
| X14 Audit and run log | run_log | cloud | platform covers part | in-house |
| X14 Audit and run log | evidence | engine | platform has nothing | in-house |
| X14 Audit and run log | model_registry | engine | platform covers part | in-house |
| X14 Audit and run log | audit_log | engine | platform covers it | - |
| X15 Replay, backfill and idempotency | mover | cloud | platform covers part | in-house |
| X15 Replay, backfill and idempotency | table_writer | engine | platform covers part | in-house |
| X15 Replay, backfill and idempotency | model_runner | engine | platform covers part | in-house |
| X15 Replay, backfill and idempotency | clock | engine | platform has nothing | in-house |
| X15 Replay, backfill and idempotency | source_reader | engine | platform has nothing | in-house |
| X15 Replay, backfill and idempotency | stream_bus | cloud | platform covers it | - |
| X15 Replay, backfill and idempotency | event_publisher | cloud | platform covers part | in-house |
| X15 Replay, backfill and idempotency | feed_writer | engine | platform covers part | in-house |
| X16 Environments, CI/CD and release | deployer | engine | platform covers part | in-house |
| X16 Environments, CI/CD and release | model_registry | engine | platform covers part | in-house |
| X16 Environments, CI/CD and release | network_boundary | cloud | platform covers it | - |
| X16 Environments, CI/CD and release | infra_provisioner | cloud | platform covers it | - |
| X17 Testing | model_runner | engine | platform covers part | in-house |
| X18 Resilience and recovery | landing_store | cloud | platform covers it | - |
| X18 Resilience and recovery | stream_bus | cloud | platform covers it | - |
| X18 Resilience and recovery | object_store | cloud | platform covers it | - |
| X19 Performance | object_store | cloud | platform covers it | - |
| X19 Performance | compute_pool | engine | platform covers it | - |
| X20 Self-healing | agent_runtime | cloud | platform covers part | in-house |
| X21 Agent assistance | agent_runtime | cloud | platform covers part | in-house |
| X22 Simulation | clock | engine | platform has nothing | in-house |

Ports bound: 44 of 44. The platform covers 18 fully, 21 in part and 5 not at all; every gap names who fills it.
Not bound on this stack: none.
Accepted gaps: GATE-02, ORCH-05.
