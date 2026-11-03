---
id: ADR-005
status: accepted
date: 2026-11-04
decision-makers: [platform owner]
consulted: [session A (practices), deck reviewers]
concerns: [X4]
dpc: [DPC-0047]
dac: [SCD-04]
plan: [G2]
source: ["deck A8"]
---

# ADR-005 History dimensions are joined as of the event

## Context and Problem Statement

A dealer changes region; a press gets a new mould. Facts must report against the version that was true when the event happened, not the current one.

## Decision Drivers

* Last year's numbers must not move when a dimension changes
* One join rule for every fact

## Considered Options

* Join to the current row
* Snapshot the dimension into the fact
* As-of join on valid-from and valid-to

## Decision Outcome

Chosen option: "As-of join on valid-from and valid-to", because it is correct for every history dimension, needs no copies, and the harness can do it for every fact.

### Consequences

* Good, because history is never rewritten by a dimension change
* Good, because the rule is in the harness, not in each fact
* Bad, because as-of joins cost more than equality joins; layout must cluster dimensions by business key

### Confirmation

A table-driven unit case: a dimension change in the middle of a window splits the fact rows correctly.

## More Information

Capabilities: DPC-0047. Obligations: SCD-04. Plan: G2. Source: deck A8.
