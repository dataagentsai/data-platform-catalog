---
id: ADR-004
status: accepted
date: 2026-11-04
decision-makers: [platform owner]
consulted: [session A (practices), deck reviewers]
concerns: [X15, X4]
dpc: [DPC-0081, DPC-0046]
dac: [DUP-02, LATE-02, DES-04, KEY-01]
plan: [G2]
source: ["deck A8 surrogate keys and SCD 2 joins"]
---

# ADR-004 Deterministic hash surrogate keys with reserved members -1 and -2

## Context and Problem Statement

Facts point at dimensions by surrogate key. Sequence or identity keys renumber when a dimension is rebuilt, so every fact points at the wrong member. Facts also arrive before their dimension member.

## Decision Drivers

* The same key on every rerun and rebuild
* No fact row lost to a late dimension
* Any fact traceable to its source row

## Considered Options

* Identity or sequence keys
* Business keys only
* A deterministic hash of source and business key, with reserved members

## Decision Outcome

Chosen option: "A deterministic hash of source and business key, with reserved members", because a hash of (source, business key), plus the version start for history dimensions, is the same on every build; -1 (unknown, not arrived yet) and -2 (not applicable) give every fact row a member to point at.

### Consequences

* Good, because rebuilds and backfills never renumber
* Good, because late members re-key on the next recompute
* Good, because orphan rate is measurable: rows on -1
* Bad, because hash collisions are possible in principle, so key uniqueness is checked per dimension
* Bad, because business keys must be kept in facts beside surrogate keys, which widens facts

### Confirmation

Gold checks: surrogate key unique per dimension, orphan rate below the fact's limit; unit tests rebuild a dimension twice and compare keys.

## More Information

Capabilities: DPC-0081, DPC-0046. Obligations: DUP-02, LATE-02, DES-04, KEY-01. Plan: G2. Source: deck A8 surrogate keys and SCD 2 joins.
