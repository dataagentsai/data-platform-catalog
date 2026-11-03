---
id: ADR-012
status: accepted
date: 2026-11-04
decision-makers: [platform owner]
consulted: [session A (practices), deck reviewers]
concerns: [X16, X11]
dpc: [DPC-0089]
dac: [ENV-01, REL-04, NAME-01]
plan: [G11]
source: ["deck A5 option A"]
---

# ADR-012 One catalog per environment and layer

## Context and Problem Statement

How to name and separate environments, layers, sources and domains in the table namespace.

## Decision Drivers

* Simple grants (analysts see production gold only)
* Storage and keys per layer
* The same shape in every environment

## Considered Options

* Catalog per environment and layer
* Catalog per environment, schema per layer
* Catalog per domain with layers as schemas
* A gold catalog per domain, later

## Decision Outcome

Chosen option: "Catalog per environment and layer", because <env>_<layer>.<schema>.<table>, with schemas per source in bronze and silver and per domain in gold, gives one storage location and key per layer and the simplest grants. A gold catalog per domain stays open if domains come to own their products.

### Consequences

* Good, because grants by layer are one line
* Good, because each environment's catalogs bind only to its own compute
* Bad, because more catalogs to create; the generator creates all of them

### Confirmation

CI rejects names that break the pattern (lower snake case, fact_ and dim_ in gold, mv_ for metric views).

## More Information

Capabilities: DPC-0089. Obligations: ENV-01, REL-04, NAME-01. Plan: G11. Source: deck A5 option A.
