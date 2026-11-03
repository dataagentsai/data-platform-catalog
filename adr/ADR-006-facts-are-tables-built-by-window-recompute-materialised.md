---
id: ADR-006
status: accepted
date: 2026-11-04
decision-makers: [platform owner]
consulted: [session A (practices), deck reviewers]
concerns: [X15, X9]
dpc: [DPC-0079, DPC-0059]
dac: [DUP-02, LATE-01, HIST-04, GOLD-01, IDEMP-01]
plan: [G2]
source: ["deck A9 gold object choice", "ETL page part 6 Gold builder"]
---

# ADR-006 Facts are tables built by window recompute; materialised views only for simple aggregates

## Context and Problem Statement

An engine can keep a materialised view up to date by itself. That is attractive, but a view cannot apply corrections, mark a window incomplete, hold the last good window when checks fail, or log a restatement.

## Decision Drivers

* Completeness, corrections and checks before publish
* One writer per fact
* Least code for simple cases

## Considered Options

* Materialised views everywhere
* Tables everywhere
* Tables by window recompute for multi-input facts; materialised views only for simple single-input aggregates

## Decision Outcome

Chosen option: "Tables by window recompute for multi-input facts; materialised views only for simple single-input aggregates", because the cases that need control get it, and the cases that do not use the engine's own refresh.

### Consequences

* Good, because corrections, completeness and restatements work for every fact that needs them
* Good, because simple aggregates need no code at all
* Bad, because two ways to build gold objects; the manifest must say which and the linter must check it

### Confirmation

The DPM linter rejects a materialised view with more than one input or with corrections switched on.

## More Information

Capabilities: DPC-0079, DPC-0059. Obligations: DUP-02, LATE-01, HIST-04, GOLD-01, IDEMP-01. Plan: G2. Source: deck A9 gold object choice; ETL page part 6 Gold builder.
