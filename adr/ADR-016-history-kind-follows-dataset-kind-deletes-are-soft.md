---
id: ADR-016
status: accepted
date: 2026-11-04
decision-makers: [platform owner]
consulted: [session A (practices), deck reviewers]
concerns: [X15, X6]
dpc: [DPC-0085, DPC-0053, DPC-0054, DPC-0017]
dac: [SCD-02, DEL-01, DEL-03, DEL-04]
plan: [G2]
source: ["ETL page history kinds and guards"]
---

# ADR-016 History kind follows dataset kind; deletes are soft

## Context and Problem Statement

Which datasets keep history, how deletes are applied, and what stops a short full copy wiping silver.

## Decision Drivers

* Most datasets need no history setting
* Facts can still find deleted members
* A short copy never deletes real rows

## Considered Options

* History chosen per dataset by hand
* History from the dataset kind, soft deletes, mass-delete guard

## Decision Outcome

Chosen option: "History from the dataset kind, soft deletes, mass-delete guard", because master data keeps type 2, transactions type 1 (type 2 where the business needs past state, with tracked columns), events append and snapshots append by date; deletes close or flag rows and never remove them; a full copy that would delete more than the declared share is held before bronze.

### Consequences

* Good, because one setting (kind) per dataset
* Good, because deleted members stay joinable
* Good, because short copies are stopped
* Bad, because every reader of silver must filter deleted rows; current views and metrics do it

### Confirmation

The tyre world plants a hard delete and a mass delete; the oracles check both.

## More Information

Capabilities: DPC-0085, DPC-0053, DPC-0054, DPC-0017. Obligations: SCD-02, DEL-01, DEL-03. Plan: G2. Source: ETL page history kinds and guards.
