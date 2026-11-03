---
id: ADR-013
status: accepted
date: 2026-11-04
decision-makers: [platform owner]
consulted: [session A (practices), deck reviewers]
concerns: [X17]
dpc: [DPC-0092, DPC-0083]
dac: [TEST-03, PURE-01]
plan: [G10, M2]
source: ["deck K05", "deck A16 borrowed from software engineering"]
---

# ADR-013 IO only at the edges; stages are pure functions

## Context and Problem Statement

Notebooks that mix reads, logic and writes cannot be unit-tested and cannot change engines.

## Decision Drivers

* Fast table-driven unit tests
* Swap engines and stores without touching logic

## Considered Options

* Logic and IO together
* Pure stages; reads and writes only at the edges, behind ports

## Decision Outcome

Chosen option: "Pure stages; reads and writes only at the edges, behind ports", because a pure function of dataframes in and dataframes out can be tested with small tables in milliseconds, and the edges are the only place an adapter is needed.

### Consequences

* Good, because unit tests per stage and per build()
* Good, because adapters change, logic does not
* Bad, because discipline: the code check must stop IO inside stages

### Confirmation

Code check: no read or write call inside a stage or build(); unit tests run without a store.

## More Information

Capabilities: DPC-0092, DPC-0083. Obligations: TEST-03, PURE-01. Plan: G10, M2. Source: deck K05; deck A16 borrowed from software engineering.
