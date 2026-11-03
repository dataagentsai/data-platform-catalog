---
id: ADR-020
status: accepted
date: 2026-11-04
decision-makers: [platform owner]
consulted: [session A (practices), deck reviewers]
concerns: [X17]
dpc: [DPC-0093]
dac: [TEST-03, TEST-05]
plan: [M5]
source: ["PLAN.html modular rules"]
---

# ADR-020 Every adapter passes its port's contract-test table

## Context and Problem Statement

Adapters for the same port must behave the same, or swapping one breaks the platform.

## Decision Drivers

* Swapping an adapter is safe
* Port invariants are tested, not just written

## Considered Options

* Each adapter tested its own way
* One contract-test table per port, run against every adapter

## Decision Outcome

Chosen option: "One contract-test table per port, run against every adapter", because each port's invariants name the DAC obligation they protect, so the table of cases comes straight from DPC and DAC, and every adapter must pass it before it can be bound.

### Consequences

* Good, because a new adapter has a ready test suite
* Good, because port invariants become executable
* Bad, because some invariants need a real store; those run as integration tests

### Confirmation

CI runs every adapter against its port's table; a binding that names an adapter without a pass fails.

## More Information

Capabilities: DPC-0093. Obligations: TEST-03, TEST-05. Plan: M5. Source: PLAN.html modular rules.
