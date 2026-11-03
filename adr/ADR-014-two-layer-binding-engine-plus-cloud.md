---
id: ADR-014
status: accepted
date: 2026-11-04
decision-makers: [platform owner]
consulted: [session A (practices), deck reviewers]
concerns: [X16, X1]
dpc: [DPC-0088]
dac: [REL-06]
plan: [M1, G3]
source: ["PLAN.html modular rules", "deck big picture, cloud version (slide 06)"]
---

# ADR-014 Two-layer binding: engine plus cloud

## Context and Problem Statement

A platform is an engine (where tables and pipelines run) on a cloud (storage, identity, keys, networks, transfer and stream services). One binding file per combination repeats the engine half for every cloud and the cloud half for every engine.

## Decision Drivers

* Moving clouds changes only the cloud half
* Moving engines changes only the engine half
* Coverage visible per combination

## Considered Options

* One binding per platform
* Two layers composed by a stack file

## Decision Outcome

Chosen option: "Two layers composed by a stack file", because each port says which layer may fill it; an engine layer and a cloud layer are written once each; a stack names one of each and a profile, says which layer wins where both bind, and coverage is generated per stack.

### Consequences

* Good, because a new cloud is one cloud file plus adapters
* Good, because a new engine is one engine file plus adapters
* Bad, because a composition step and its linter to maintain

### Confirmation

The DBS linter checks every layer binds only ports allowed for its layer, and every stack resolves every double binding.

## More Information

Capabilities: DPC-0088. Obligations: REL-06. Plan: M1, G3. Source: PLAN.html modular rules; deck big picture, cloud version (slide 06).
