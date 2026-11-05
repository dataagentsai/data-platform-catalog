---
id: ADR-026
status: accepted
date: 2026-11-05
decision-makers: [platform owner]
consulted: [Application Architecture deck review]
concerns: [X15]
dpc: []
dac: []
plan: [G10, M2]
source: ["Application Architecture deck, slide Bronze to Silver"]
---

# ADR-026 Silver runs as PySpark on job compute, not as a Declarative Pipeline with AUTO CDC

## Context and Problem Statement

Bronze to silver needs ordering by change sequence, deletes and SCD 1 or 2 history. Databricks offers this as AUTO
CDC (formerly APPLY CHANGES), but only inside Lakeflow Declarative Pipelines (formerly Delta Live Tables). Our engine
already does it with thirteen processors and a MERGE, equal to the oracle on all 14 tyre days.

## Decision Drivers

* Cost: AUTO CDC needs the Pro edition, and the quality rules (expectations) the Advanced edition; pipeline compute costs more per unit than job compute
* Portability: the same processors run on DuckDB in CI and on other engines (ADR-013)
* Recovery: void one batch and rebuild (ADR-025), not a whole-table refresh

## Considered Options

* A. Our thirteen processors in PySpark, our MERGE, run as a Lakeflow Job task on job compute
* B. Our processors inside a Declarative Pipeline, history by AUTO CDC
* C. Fully declarative (SQL and expectations only)

## Decision Outcome

Chosen option: "A", because it is already built and tested, runs on cheaper job compute, stays portable, and keeps
per-batch reruns. B and C are recorded as considered and dropped.

### Consequences

* Good, because no pipeline-edition cost and one code path everywhere
* Good, because adding a processor is one function behind one interface, registered and switched on in metadata
* Bad, because we own the SCD and ordering code and its tests
* Bad, because no pipeline graph or event log; our run log and ops dashboards cover them

### Confirmation

Silver equals the oracle on all 14 days on Spark and DuckDB. Tables are liquid-clustered: bronze by batch key (reads
skip old files), silver by business key (the MERGE rewrites only touched files). Write modes per dataset: append,
SCD 1, SCD 2, snapshot window; full overwrite to be added as a snapshot whose window is the whole table.

## More Information

Revisit if Databricks makes AUTO CDC available on job compute at job-compute prices.
