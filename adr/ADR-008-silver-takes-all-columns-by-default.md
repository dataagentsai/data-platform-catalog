---
id: ADR-008
status: accepted
date: 2026-11-04
decision-makers: [platform owner]
consulted: [session A (practices), deck reviewers]
concerns: [X3]
dpc: [DPC-0045, DPC-0008]
dac: [SCH-01, PROJ-01]
plan: [G2]
source: ["ETL page transform decision D1 (changed 3 Nov)"]
---

# ADR-008 Silver takes all columns by default

## Context and Problem Statement

Should silver hold every column the source sends, or only the columns someone listed?

## Decision Drivers

* Analysts should not wait for a release to see a column
* Silver's names and types are ours
* Personal data must never pass unclassified

## Considered Options

* Listed columns only (declared)
* All columns except excluded ones
* Per source

## Decision Outcome

Chosen option: "All columns except excluded ones, with 'declared' available per dataset", because most new columns are harmless and wanted; a dataset that needs a strict shape can still declare its list; personal-data sources hold files with an unknown column until the contract classifies it.

### Consequences

* Good, because new columns reach silver without a release
* Good, because strict datasets keep a strict shape
* Bad, because silver can grow columns nobody uses
* Bad, because personal-data sources still need the hold rule

### Confirmation

Contract check: an added column on a personal-data source holds the file and alerts; elsewhere it is noted and loaded.

## More Information

Capabilities: DPC-0045, DPC-0008. Obligations: SCH-01, PROJ-01. Plan: G2. Source: ETL page transform decision D1 (changed 3 Nov).
