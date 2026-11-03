---
id: ADR-001
status: accepted
date: 2026-11-04
decision-makers: [platform owner]
consulted: [session A (practices), deck reviewers]
concerns: [X13, X7]
dpc: [DPC-0074, DPC-0049]
dac: [FLOW-01, SCD-04]
plan: [G2]
source: ["deck A5 catalog and schema design", "ETL page part 5 Conformer"]
---

# ADR-001 Silver is source-aligned; conforming happens in gold

## Context and Problem Statement

Several sources describe the same things (an order in the ERP, its production in the manufacturing system, its quality result in the lab system). Somewhere they must be joined and their codes made to agree. The question is in which layer.

## Decision Drivers

* One source feeds many domains, so silver cannot belong to one domain
* A source outage must not stop other sources' silver
* Conforming rules change with the business; cleaning rules do not

## Considered Options

* Silver source-aligned; conform in gold
* Silver conformed by domain (joins across sources in silver)
* A separate integration layer between silver and gold

## Decision Outcome

Chosen option: "Silver source-aligned; conform in gold", because silver then has one meaning (one source, cleaned, typed, with history) and the generic engine can build every silver table from metadata alone; cross-source logic lives in one place, the gold harness.

### Consequences

* Good, because silver is built per source by one generic engine, with no business logic
* Good, because a broken source blocks only its own silver tables
* Good, because shared dimensions are conformed once, in gold, and reused by every fact
* Bad, because consumers wanting a cross-source view must wait for gold
* Bad, because mapping tables for codes become a gold input that needs a steward

### Confirmation

The lineage check rejects any silver table that reads from more than one source's bronze (FLOW-01).

## More Information

Capabilities: DPC-0074, DPC-0049. Obligations: FLOW-01, SCD-04. Plan: G2. Source: deck A5 catalog and schema design; ETL page part 5 Conformer.
