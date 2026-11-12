---
id: ADR-031
status: accepted
date: 2026-11-12
decision-makers: [platform owner]
consulted: []
concerns: [X3, X19]
dpc: [DPC-0023, DPC-0007, DPC-0041]
dac: [RAW-01, SCH-01, SCH-02]
plan: [16f, B3]
source: ["12 Nov session: row or column oriented, which formats"]
---

# ADR-031 Row formats to move data, columnar files to store it; landing keeps what arrived

## Context and Problem Statement

Data reaches us as device messages, change-capture files, partner files and API pages, in many formats. Which format
belongs at which hop, and do we convert on the way in?

## Decision Drivers

* Moving one record at a time and analysing many rows have opposite needs
* Landing must keep deliveries as received, for replay (DPC-0023, RAW-01)
* A sender's schema change must not silently break readers (SCH-01, SCH-02)
* Every conversion before the live lane adds delay

## Considered Options

* A. Convert everything to one format at the front door
* B. Per hop: row formats with a registered schema to move records; deliveries kept as they arrived in landing; columnar files under an open table format from bronze on
* C. Keep text formats everywhere for simplicity

## Decision Outcome

Chosen option: "B".

| Hop | Format |
|---|---|
| Device or app to the front door | a row format: text with a declared shape, or a compact binary row format where bandwidth or message cost matters; the schema is registered and versioned |
| Live lane | whatever arrived; no conversion |
| Landing | as delivered; senders that batch are asked for a columnar file (change capture, buffered streams), with types and nulls kept |
| Bronze, silver, gold | columnar files under the open table format (ADR-027) |

The lander reads every delivered format the binding lists (text lines, delimited text, columnar files, and row
formats with a registry); the format is the dataset setting `file_format_data`. The landing format is a benchmark
axis (ADR-030).

### Consequences

* Good, because each hop uses the format that suits it
* Good, because replay always reads exactly what arrived
* Bad, because the lander needs a reader per delivered format

### Confirmation

The world delivers the same rows as text lines, delimited text and columnar files; bronze and silver totals are equal
for all three; a sender adding a column passes, renaming one is held (SCH-02).

## More Information

Products for each format are named in the engine binding (`dbs/engine/`) (`lander`) and the cloud binding (`dbs/cloud/`) (`movers`).
