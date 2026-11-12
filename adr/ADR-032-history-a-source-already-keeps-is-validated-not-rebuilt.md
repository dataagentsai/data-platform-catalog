---
id: ADR-032
status: accepted
date: 2026-11-12
decision-makers: [platform owner]
consulted: [tyre client brief]
concerns: [X15, X4]
dpc: [DPC-0085, DPC-0025, DPC-0011]
dac: [SCD-02, SCD-04]
plan: [16b, F3, B6]
source: ["12 Nov session: the ERP sometimes already delivers type 2 history"]
---

# ADR-032 History a source already keeps is validated, not rebuilt: a fifth history kind, source-versioned

## Context and Problem Statement

ADR-016 sets history by dataset kind: SCD type 2, type 1, append, or snapshot. Some sources (an ERP's
validity-dated tables) already deliver every version with its own valid-from and valid-to. Running our type 2 logic on
them doubles history or overwrites the source's dates. What does silver do with history it did not build?

## Decision Drivers

* The source's validity dates are the business truth; ours would be arrival-based guesses
* Bad source history (overlaps, gaps, two current rows) must be caught, not trusted blindly
* Gold's as-of joins (ADR-005, SCD-04) must work the same on either kind of history

## Considered Options

* A. Treat it as type 2 and rebuild history from change order
* B. Treat it as append and leave the dates unchecked
* C. A fifth history kind, `source_versioned`: keep the source's versions and dates, and validate them

## Decision Outcome

Chosen option: "C". The dataset declares `history_kind: source_versioned` and names its validity columns. Silver keeps
each version as delivered, maps the source's columns to the standard validity columns, and checks per key: no two
versions overlap, no gap unless the source declares gaps allowed, exactly one current version (or none, if deleted).
A key that fails is quarantined with the rule that failed (DPC-0011); the other keys load. Reruns change nothing
(version keys come from the data).

### Consequences

* Good, because the source's history is kept exactly and checked
* Good, because gold sees the same standard validity columns from every history kind
* Bad, because a sixth case for the history stage and its tests

### Confirmation

The world adds a validity-dated material table with one planted overlap and one planted gap; silver keeps the good
keys, quarantines the two bad ones with their reasons, and gold's as-of joins equal the oracle.

## More Information

Extends ADR-016. Settings: `history_kind`, `valid_from_column`, `valid_to_column`, `gaps_allowed`.
