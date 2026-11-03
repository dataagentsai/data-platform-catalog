---
id: ADR-007
status: accepted
date: 2026-11-04
decision-makers: [platform owner]
consulted: [session A (practices), deck reviewers]
concerns: [X4, X1]
dpc: [DPC-0045]
dac: [DQ-02, CFG-01, LATE-04, ENG-01]
plan: [G2, G5]
source: ["deck A7", "ETL page STAGES, decisions D5 and D8 there"]
---

# ADR-007 Thirteen standard stages from bronze to silver

## Context and Problem Statement

Every source needs the same kinds of cleaning. Written per table, the same date format is parsed four ways and none is tested.

## Decision Drivers

* One engine for every table
* A new table is new metadata, never new code
* No value silently lost

## Considered Options

* Per-table cleaning queries
* Free-form expressions in metadata
* A fixed list of generic stages, configured per column

## Decision Outcome

Chosen option: "A fixed list of generic stages, configured per column", because thirteen stages in a fixed order (contract check; projection, extract and rename; hygiene; parse and type; time; standardise values; personal data; row filter; quality rules; duplicates; keys; history and deletes; provenance) cover the sources seen so far, each is a tested pure function, and a new need becomes a new generic stage.

### Consequences

* Good, because every table is cleaned the same way, by tested code
* Good, because per-column settings are reviewable in YAML
* Bad, because rare needs wait for a new stage, or move to gold
* Bad, because no free-form query between bronze and silver

### Confirmation

The engine refuses settings outside the stage list; every stage has table-driven unit tests.

## More Information

Capabilities: DPC-0045. Obligations: DQ-02, CFG-01, LATE-04, ENG-01. Plan: G2, G5. Source: deck A7; ETL page STAGES, decisions D5 and D8 there.
