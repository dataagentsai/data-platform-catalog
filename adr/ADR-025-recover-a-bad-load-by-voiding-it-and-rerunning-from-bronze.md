---
id: ADR-025
status: accepted
date: 2026-11-05
decision-makers: [platform owner]
consulted: [design discussion 5 Nov]
concerns: [X15, X18]
dpc: [DPC-0054, DPC-0082]
dac: [DEL-04, HIST-05]
plan: [G5, G7]
source: ["design discussion 5 Nov: how to roll back a bad load"]
---

# ADR-025 Recover a bad load by voiding it and rerunning from bronze

## Context and Problem Statement

A bad delivery can get past the checks, for example a short full copy that marks hundreds of records deleted. When it
is found days later, later good loads have built on it. Restoring tables to an older version throws those good loads
away, and a planner that restores and replays per table is complex to build and to trust.

## Decision Drivers

* Use what the platform already guarantees: bronze is never changed, silver is derived from bronze, gold windows are
  replaced, writes are repeatable
* One engine and one run log for normal runs and recovery
* Simple enough for an on-call engineer to run and trust

## Considered Options

* Restore every affected table to a version before the bad load
* A recovery planner that restores each table and replays later batches in dependency order
* Void the bad batch, rebuild the affected silver table from bronze, rerun the gold windows that use it

## Decision Outcome

Chosen option: "Void the bad batch, rebuild the affected silver table from bronze, rerun the gold windows that use
it", because silver is purely derived from bronze and gold windows are replaced, so a rerun that skips the bad batch
gives exactly the right answer with no new machinery. The batch gets a `void` status in the file log with the reason
and the approver, and every read skips it. Validation is the normal recon per hop and the known answers.
Rebuilding only the affected days is an optimisation added later, and only for a table too large to rebuild whole.
A table restore stays an emergency option for a bad write caught before any later load.

### Consequences

* Good, because recovery is an ordinary run: same engine, same checks, same run log
* Good, because later good loads are kept
* Bad, because a whole-table rebuild costs more for very large tables, until the per-day optimisation is needed

### Confirmation

A world scenario lets the day-9 short material copy past the guard, voids it, rebuilds silver from bronze and reruns
gold; recon per hop and the known answers pass, and the day-10 and day-11 changes are still present.

## More Information

Capabilities: DPC-0054, DPC-0082. Obligations: DEL-04, HIST-05. Plan: G5, G7. Built in W1 part W1f.
