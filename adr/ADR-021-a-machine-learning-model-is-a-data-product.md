---
id: ADR-021
status: accepted
date: 2026-11-04
decision-makers: [platform owner]
consulted: [session A (practices), deck reviewers]
concerns: [X13, X9]
dpc: [DPC-0077, DPC-0050, DPC-0061]
dac: [CFG-03, LIN-01, PERF-02]
plan: [D16]
source: ["PLAN.html D16"]
---

# ADR-021 A machine-learning model is a data product

## Context and Problem Statement

Models need owners, contracts, lineage and monitoring, as data products do. A separate spec family for ML would duplicate most of the data family.

## Decision Drivers

* No new spec family
* The same owner, lineage and gate rules as other products

## Considered Options

* A separate ML spec family
* A model entry in the manifest (a model card) plus ML obligations in DAC

## Decision Outcome

Chosen option: "A model entry in the manifest (a model card) plus ML obligations in DAC", because the manifest already says what this company does per dataset; a model is one more entry, with features from gold, a target, a metric with a threshold, monitoring and limits.

### Consequences

* Good, because models follow the same review, gates and evidence
* Good, because lineage reaches from source to prediction
* Bad, because dAC needs ML obligations (proposed to session A)

### Confirmation

The DPM linter checks every model's features and target resolve to gold or feature tables.

## More Information

Capabilities: DPC-0077, DPC-0050, DPC-0061. Obligations: CFG-03, LIN-01, PERF-02. Plan: D16. Source: PLAN.html D16.
