---
id: ADR-026
status: accepted
date: 2026-11-05
decision-makers: [platform owner]
consulted: [Application Architecture deck review]
concerns: [X15]
dpc: [DPC-0085, DPC-0025]
dac: [SCD-02]
plan: [G10, M2]
source: ["Application Architecture deck, slide Bronze to Silver"]
---

# ADR-026 Silver runs as our own stages on job compute, not as the engine's declarative pipeline with managed change capture

## Context and Problem Statement

Bronze to silver needs ordering by change sequence, deletes and SCD 1 or 2 history. The engine offers this as a
managed change-capture feature, but only inside its declarative pipeline product. Our engine already does it with
thirteen processors and a MERGE, equal to the oracle on all 14 tyre days. (The binding names the products.)

## Decision Drivers

* Cost: the managed change-capture feature needs a higher pipeline edition, and its quality rules a higher one still; pipeline compute costs more per unit than job compute
* Portability: the same processors run on the laptop engine in CI and on other engines (ADR-013)
* Recovery: void one batch and rebuild (ADR-025), not a whole-table refresh

## Considered Options

* A. Our thirteen processors, our MERGE, run as a job task on job compute
* B. Our processors inside the declarative pipeline, history by the managed change-capture feature
* C. Fully declarative (SQL and pipeline expectations only)

## Decision Outcome

Chosen option: "A", because it is already built and tested, runs on cheaper job compute, stays portable, and keeps
per-batch reruns. B and C are recorded as considered and dropped.

### Consequences

* Good, because no pipeline-edition cost and one code path everywhere
* Good, because adding a processor is one function behind one interface, registered and switched on in metadata
* Good, because the table format stays a binding choice (ADR-027): the declarative pipeline writes only its own format
* Bad, because we own the SCD and ordering code and its tests
* Bad, because no pipeline graph or event log; our run log and ops dashboards cover them

### Confirmation

Silver equals the oracle on all 14 days on both engines. Tables are clustered automatically: bronze by batch key
(reads skip old files), silver by business key (the MERGE rewrites only touched files). Write modes per dataset:
append, SCD 1, SCD 2, snapshot window; full overwrite to be added as a snapshot whose window is the whole table.

## More Information

Revisit if the managed change-capture feature becomes available on job compute at job-compute prices. Product names
for this decision live in the engine binding (`dbs/engine/`) (silver writer).
