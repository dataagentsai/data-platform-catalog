---
id: ADR-009
status: accepted
date: 2026-11-04
decision-makers: [platform owner]
consulted: [session A (practices), deck reviewers]
concerns: [X4, X8]
dpc: [DPC-0042, DPC-0056]
dac: [DQ-01, DQ-02, OPS-01, SEV-01, QUAR-01]
plan: [G2, G7]
source: ["deck A13 and A14"]
---

# ADR-009 Quality severity sets the action

## Context and Problem Statement

Every rule failure treated the same way either pages too much or blocks too much.

## Decision Drivers

* Bad rows never silently pass
* Alerts people will not mute
* Authors choose intent, not mechanics

## Considered Options

* Every failure stops the load
* Every failure warns
* Three severities, each with a declared action

## Decision Outcome

Chosen option: "Three severities, each with a declared action", because critical quarantines the rows and blocks the dataset or holds the gold window and pages on-call; major quarantines and alerts the owner; minor keeps the row, flags it and goes into a daily digest. Authors pick a severity; the platform does the rest.

### Consequences

* Good, because consistent behaviour for every rule
* Good, because noise falls without hiding anything critical
* Bad, because severity must be chosen well; defaults per rule kind help

### Confirmation

The DPM linter requires an action for every severity the contract uses; a planted critical failure in the tyre world must block and page.

## More Information

Capabilities: DPC-0042, DPC-0056. Obligations: DQ-01, DQ-02, OPS-01, SEV-01, QUAR-01. Plan: G2, G7. Source: deck A13 and A14.
