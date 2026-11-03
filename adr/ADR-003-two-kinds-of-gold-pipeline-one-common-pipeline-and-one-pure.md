---
id: ADR-003
status: accepted
date: 2026-11-04
decision-makers: [platform owner]
consulted: [session A (practices), deck reviewers]
concerns: [X15, X1, X17]
dpc: [DPC-0083, DPC-0084, DPC-0080]
dac: [DUP-02, LATE-01, DES-04, PURE-01, ENG-01]
plan: [D18, R3, D6]
source: ["deck K05 Silver to Gold", "deck A9"]
---

# ADR-003 Two kinds of gold pipeline: one common pipeline, and one pure build() per modelled fact

## Context and Problem Statement

Gold holds two very different kinds of table. Many are one silver table reshaped (renamed, keyed, history kept). A few are modelled facts that join several inputs and carry real business logic (OTIF, scrap rate). Writing every gold table as its own pipeline gives hundreds of drifting copies; forcing facts into configuration gives an unreadable rule language.

## Decision Drivers

* No per-table code where metadata is enough
* Business logic readable and unit-testable
* Late data, corrections and reruns handled the same way for every fact

## Considered Options

* Every gold table hand-written
* Everything configuration-driven
* A common pipeline for one-to-one tables, and a harness that calls one pure build() per modelled fact

## Decision Outcome

Chosen option: "A common pipeline for one-to-one tables, and a harness that calls one pure build() per modelled fact", because configuration covers the common case, and for facts the only code a person writes is the business logic: a set-based query model or a pure dataframe function. The harness owns change detection, full reads of changed windows, key lookup, checks and the window replace.

### Consequences

* Good, because a fact is one small pure function with table-driven tests
* Good, because the harness is tested once, for every fact
* Good, because rule R3 holds: generators write pipelines, and the only hand-written code is a declared build()
* Bad, because two shapes of gold pipeline to teach
* Bad, because the harness is a significant piece of our own code to keep

### Confirmation

The DPM linter requires a build reference for every modelled fact and forbids one for one-to-one tables; the code check rejects IO inside build().

## More Information

Capabilities: DPC-0083, DPC-0084, DPC-0080. Obligations: DUP-02, LATE-01, DES-04, PURE-01, ENG-01. Plan: D18, R3, D6. Source: deck K05 Silver to Gold; deck A9.
