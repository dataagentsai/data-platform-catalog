---
id: ADR-019
status: accepted
date: 2026-11-04
decision-makers: [platform owner]
consulted: [session A (practices), deck reviewers]
concerns: [X1]
dpc: [DPC-0035, DPC-0001]
dac: [CFG-01]
plan: [M3, M4, R1]
source: ["PLAN.html modular rules"]
---

# ADR-019 Domains are data; one manifest drives every cloud

## Context and Problem Statement

The shop and the tyre company must run on the same code, and one company must run on any stack.

## Decision Drivers

* No domain words in framework code or specs
* No cloud words in manifests

## Considered Options

* A fork per domain or cloud
* Domains as manifests and worlds; clouds as bindings

## Decision Outcome

Chosen option: "Domains as manifests and worlds; clouds as bindings", because a domain is a folder of manifests, contracts and a world; a cloud is a binding; the generator for a stack turns the same manifest into that stack's jobs.

### Consequences

* Good, because a second domain proves the framework is domain-free
* Good, because moving cloud does not touch the manifest
* Bad, because manifests may not use cloud-specific keys; some registered keys must be generalised

### Confirmation

The product-name linter on manifests and worlds; the same tyre manifest validates for every stack.

## More Information

Capabilities: DPC-0035, DPC-0001. Obligations: CFG-01. Plan: M3, M4, R1. Source: PLAN.html modular rules.
