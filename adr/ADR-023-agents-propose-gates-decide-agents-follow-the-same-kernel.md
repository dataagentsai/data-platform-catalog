---
id: ADR-023
status: accepted
date: 2026-11-04
decision-makers: [platform owner]
consulted: [session A (practices), deck reviewers]
concerns: [X21, X20]
dpc: [DPC-0100, DPC-0101, DPC-0102]
dac: [GATE-03, HEAL-01]
plan: [M6, G13]
source: ["PLAN.html modular rules", "deck agentic solutions"]
---

# ADR-023 Agents propose, gates decide; agents follow the same kernel and adapter split

## Context and Problem Statement

Triage, self-healing and ask-your-data agents are useful and risky. They must not become a side door into production.

## Decision Drivers

* Every change through the same gates
* Agents portable across clouds like the rest

## Considered Options

* Agents act directly
* Agents propose manifest pull requests; the harness kernel is cloud-free

## Decision Outcome

Chosen option: "Agents propose manifest pull requests; the harness kernel is cloud-free", because agents read evidence through declared tools and propose changes; tests and reviewers decide; model, gateway and runtime are adapters, as in the AI family's harness.

### Consequences

* Good, because no agent action skips a gate
* Good, because agents move clouds with the binding
* Bad, because slower fixes than direct action; urgent fixes still need a person

### Confirmation

The manifest lists enabled agents and their autonomy; a test plants a fix that would loosen a contract and checks the gate stops it.

## More Information

Capabilities: DPC-0100, DPC-0101, DPC-0102. Obligations: GATE-03, HEAL-01. Plan: M6, G13. Source: PLAN.html modular rules; deck agentic solutions.
