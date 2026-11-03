---
id: ADR-011
status: accepted
date: 2026-11-04
decision-makers: [platform owner]
consulted: [session A (practices), deck reviewers]
concerns: [X19, X10]
dpc: [DPC-0098]
dac: [PERF-05]
plan: [G8]
source: ["deck K03 storage"]
---

# ADR-011 Table layout: automatic clustering and automatic maintenance

## Context and Problem Statement

Partitioning by hand needs choices nobody revisits, and maintenance jobs need owners.

## Decision Drivers

* Good layout without per-table tuning
* No maintenance jobs to write and own

## Considered Options

* Partitions chosen by hand and scheduled compaction
* Clustering keys chosen by hand
* Clustering chosen automatically from queries, and the platform's automatic maintenance

## Decision Outcome

Chosen option: "Clustering chosen automatically from queries, and the platform's automatic maintenance", because the engine sees the queries and can choose better than a one-off guess; scheduled maintenance remains only where automatic maintenance is off.

### Consequences

* Good, because no layout decisions per table
* Good, because no maintenance jobs to own
* Bad, because depends on the engine offering both; the binding records coverage and the fallback

### Confirmation

The binding marks table_writer layout coverage; a nightly check reports tables with small-file counts above the limit.

## More Information

Capabilities: DPC-0098. Obligations: PERF-05. Plan: G8. Source: deck K03 storage.
