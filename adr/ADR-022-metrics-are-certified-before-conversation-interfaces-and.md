---
id: ADR-022
status: accepted
date: 2026-11-04
decision-makers: [platform owner]
consulted: [session A (practices), deck reviewers]
concerns: [X13]
dpc: [DPC-0073, DPC-0076]
dac: [SERV-04]
plan: [G6]
source: ["deck A12"]
---

# ADR-022 Metrics are certified before conversation interfaces and agents use them

## Context and Problem Statement

A plain-word interface answers with confidence, right or wrong. It must use only metrics someone has checked.

## Decision Drivers

* The same number everywhere
* No confident wrong answers

## Considered Options

* Any metric
* Certified metrics only, with a lifecycle (draft, reviewed, certified, deprecated)

## Decision Outcome

Chosen option: "Certified metrics only, with a lifecycle (draft, reviewed, certified, deprecated)", because each metric declares its time dimension, whether it may be summed, synonyms and a known-answer test; only certified metrics reach conversation interfaces and agents.

### Consequences

* Good, because answers trace to one reviewed definition
* Good, because synonyms map business words to the right metric
* Bad, because certification is a step metric owners must take

### Confirmation

The DPM linter rejects a certified metric without a known-answer test; the conversation binding reads only certified metrics.

## More Information

Capabilities: DPC-0073, DPC-0076. Obligations: SERV-04. Plan: G6. Source: deck A12.
