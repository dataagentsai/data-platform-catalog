---
id: ADR-015
status: accepted
date: 2026-11-04
decision-makers: [platform owner]
consulted: [session A (practices), deck reviewers]
concerns: [X1, X17]
dpc: [DPC-0093]
dac: [TEST-03, TEST-05]
plan: [M2, R4]
source: ["PLAN.html modular rules", "LakeIngestionFramework realms"]
---

# ADR-015 Kernel, ports, adapters and realms

## Context and Problem Statement

The framework must run on more than one engine and cloud without branches on which one it is.

## Decision Drivers

* No vendor branches in kernel code
* Each vendor's SDK imported in one place

## Considered Options

* Branches per platform
* Kernel, ports, adapters, and a realm per engine-cloud pair

## Decision Outcome

Chosen option: "Kernel, ports, adapters, and a realm per engine-cloud pair", because the kernel is pure and cloud-free; it calls ports; each adapter implements one port for one product; a realm wires the adapters a stack's binding names, and nothing else knows which product is in use.

### Consequences

* Good, because the kernel is tested once
* Good, because a realm is small and generated from the binding
* Bad, because ports must be designed carefully; a leaky port drags vendor detail into the kernel

### Confirmation

Import check: vendor SDKs only under adapters; contract tests per port (ADR-020).

## More Information

Capabilities: DPC-0093. Obligations: TEST-03, TEST-05. Plan: M2, R4. Source: PLAN.html modular rules; LakeIngestionFramework realms.
