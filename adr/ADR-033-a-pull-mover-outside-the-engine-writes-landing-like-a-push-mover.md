---
id: ADR-033
status: accepted
date: 2026-11-12
decision-makers: [platform owner]
consulted: []
concerns: [X3, X15, X12]
dpc: [DPC-0038, DPC-0037, DPC-0023]
dac: [ING-01, RAW-01]
plan: [16a, GP2]
source: ["12 Nov session: pull ingestion on the cloud's own serverless jobs and functions, not our in-engine puller"]
---

# ADR-033 A pull mover outside the engine writes landing like a push mover

## Context and Problem Statement

ADR-002 says pulled data skips landing: our own puller runs the lander steps in process and writes bronze. The user
now wants pulls done by the cloud's own serverless jobs (databases) and functions (APIs). Those run outside the
engine; if they wrote bronze directly, the tables would be written outside the catalog of record (ADR-028) and outside
the lander's steps (ING-01).

## Decision Drivers

* Every way into bronze passes the same entry steps (ING-01)
* One writer per table and one catalog of record (ADR-028)
* A replay copy should exist for what an outside mover delivered

## Considered Options

* A. The outside mover writes bronze directly, re-implementing the lander steps
* B. The outside mover writes landing and meets the landing contract (DPC-0038), exactly like a push mover; our lander takes it from there
* C. Drop outside movers and keep only our in-engine puller

## Decision Outcome

Chosen option: "B". An outside pull mover is a push mover from the platform's point of view: it writes each delivery
once, under a unique name, manifest last, into landing. ADR-002 still holds for our own in-engine puller. The cost is
a landing copy of pulled personal data, limited by ADR-029's short archive for such datasets.

### Consequences

* Good, because one set of entry steps and one writer for bronze
* Good, because the delivery is kept for replay
* Bad, because a landing copy of pulled personal data exists for up to its retention limit

### Confirmation

The outside movers' adapters pass the same landing contract table the local movers pass; a pulled table loads to
bronze with the same totals as through the in-engine puller.

## More Information

Products: the cloud binding (`dbs/cloud/`) (`movers`). Does not supersede ADR-002; narrows it to the in-engine puller.
