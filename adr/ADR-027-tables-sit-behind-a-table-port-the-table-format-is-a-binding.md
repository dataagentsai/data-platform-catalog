---
id: ADR-027
status: accepted
date: 2026-11-12
decision-makers: [platform owner]
consulted: [tyre client brief]
concerns: [X15, X17, X19]
dpc: [DPC-0024, DPC-0006, DPC-0093, DPC-0098]
dac: [DUP-02, RAW-01, PERF-05]
plan: [16b, 16d, B2]
source: ["12 Nov session: client asks for an open table format; user: one small IO adapter per format, then benchmark"]
---

# ADR-027 Tables sit behind a table port; the open table format is a binding choice

## Context and Problem Statement

The engine writes bronze, silver and gold through adapters that call one table format directly (five adapter files;
the stages and gold logic are pure, ADR-013). A client now asks for a different open table format, and the user wants
to compare the three common open formats on the same workload. How do we change format without touching the stages,
and keep "a rerun changes nothing" (DUP-02) when the format's own idempotent-write feature is not there?

## Decision Drivers

* The stages, history logic and gold harness must not change when the format changes
* Idempotent writes must not depend on a feature only one format has
* Every format must prove the same behaviour, not "probably the same"
* Upkeep (compaction, old-version expiry) differs per format and must not be forgotten
* A fair benchmark: same engine, same data, same checks, only the format varies

## Considered Options

* A. Keep calling one format directly in the adapters; fork adapters per client
* B. A table port with five operations, one small adapter per format, tables addressed by catalog name, and our file log as the authority for "already written"
* C. Write one format and expose it as another through a compatibility layer

## Decision Outcome

Chosen option: "B", because only B keeps the stages untouched and makes every format pass one contract table. The
port has five operations: **read** (current rows or a window), **append a batch** (idempotent by batch key: the
adapter first asks our file log whether the batch key is committed, so a rerun writes nothing), **merge** (rows with
an action column: upsert or delete), **replace a window** (gold, ADR-006), and **upkeep** (compaction, old-version
expiry, statistics; a no-op where the platform does it automatically). Tables are addressed as
`catalog.schema.table`, never by folder path. The format is the setting `table_format`, per environment with a
per-dataset override; the binding sets the default. C stays available as a binding option where a client wants one
format read as another, but it is not the design.

### Consequences

* Good, because a new format is one adapter plus one row in the binding
* Good, because idempotency rests on our file log, which every format and every engine shares
* Good, because the benchmark varies one axis only
* Bad, because three adapters to keep passing the contract table
* Bad, because format-specific speed-ups (for example a format's own change feed) are not used by the stages; an adapter may use them internally only

### Confirmation

One contract table (ADR-020) runs against every format adapter: append twice gives one copy; merge with late and
deleted rows gives the expected history; replace window leaves other windows untouched; upkeep leaves row counts and
totals unchanged. The tyre world's 14 days give the same silver and gold totals on every format.

## More Information

Supersedes nothing; extends ADR-013 (IO only at the edges) and ADR-015 (kernel, ports, adapters). The binding
(the engine binding, `table_store`) names the formats and the default. Benchmark plan: TODO B14.
