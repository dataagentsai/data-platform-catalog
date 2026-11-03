---
id: ADR-017
status: accepted
date: 2026-11-04
decision-makers: [platform owner]
consulted: [session A (practices), deck reviewers]
concerns: [X15]
dpc: [DPC-0082]
dac: [HIST-04, LATE-01, HIST-05]
plan: [G2]
source: ["ETL page guards"]
---

# ADR-017 Corrections live in their own table and reach gold through a backfill plan

## Context and Problem Statement

A change is something new in the world; a correction says an old value was wrong. Silver must keep what the source said, and gold must show the corrected value, without anyone editing gold.

## Decision Drivers

* Silver stays faithful to the source
* No hand fixes in gold
* A correction never restates months by surprise

## Considered Options

* Edit silver
* Edit gold
* A corrections table laid over silver by the window recompute, activated by a backfill plan

## Decision Outcome

Chosen option: "A corrections table laid over silver by the window recompute, activated by a backfill plan", because corrections are reviewable rows with who and why; only the recompute reads them; the plan says which windows to rebuild and when.

### Consequences

* Good, because every corrected number is explainable
* Good, because restatements are logged and scheduled
* Bad, because materialised views cannot read corrections; facts that need them are built by recompute (ADR-006)

### Confirmation

The tyre world plants a correction; the oracle checks only the planned windows changed.

## More Information

Capabilities: DPC-0082. Obligations: HIST-04, LATE-01. Plan: G2. Source: ETL page guards.
