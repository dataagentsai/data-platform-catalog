---
id: ADR-010
status: accepted
date: 2026-11-04
decision-makers: [platform owner]
consulted: [session A (practices), deck reviewers]
concerns: [X1, X14]
dpc: [DPC-0033, DPC-0034, DPC-0021]
dac: [CFG-01, REL-01, CFG-03, CFG-04, CFG-05]
plan: [D10, G5]
source: ["deck K09b metadata store", "the metadata DB design adopted 27 Oct"]
---

# ADR-010 The metadata store is a relational database reached only through stored procedures

## Context and Problem Statement

Jobs need configuration and run state with transactions; people need reviewable files. Slice 1 kept both in tables of the lakehouse itself.

## Decision Drivers

* Review in version control
* Transactions for watermark and run record together
* One stable interface whatever the keys

## Considered Options

* Files only
* Lakehouse tables
* A relational database with stored procedures as the only way in, fed from files by a validating loader

## Decision Outcome

Chosen option: "A relational database with stored procedures as the only way in, fed from files by a validating loader", because the database gives transactions and foreign keys, the procedures and reader views give every engine one stable interface, and only the loader writes configuration, from reviewed files.

### Consequences

* Good, because watermark and run record commit together
* Good, because any engine can read the same views
* Good, because dashboards read the store directly
* Bad, because a database to run, back up and replicate
* Bad, because the procedures are an API to version

### Confirmation

Static check: no service code writes metadata tables except through the procedures; the binding names the database product.

## More Information

Capabilities: DPC-0033, DPC-0034, DPC-0021. Obligations: CFG-01, REL-01, CFG-03, CFG-04, CFG-05. Plan: D10, G5. Source: deck K09b metadata store; the metadata DB design adopted 27 Oct.
