---
id: ADR-034
status: accepted
date: 2026-11-12
decision-makers: [platform owner]
consulted: []
concerns: [X8, X9]
dpc: [DPC-0020, DPC-0022, DPC-0057]
dac: [PERF-02, SERV-02, REC-05]
plan: [16f, B4, B10]
source: ["12 Nov session, user: end-to-end timing and also hop to hop"]
---

# ADR-034 Every hop stamps its own time; delay is reported end to end and per hop, measured or modeled

## Context and Problem Statement

A freshness promise ("gold within 75 minutes", "alerts within 5 seconds") is broken somewhere along a path of many
hops. One end-to-end number says that it broke, not where. Benchmarks of golden paths (ADR-030) also need per-hop
numbers, and some hops cannot be run locally.

## Decision Drivers

* Find the hop that broke a promise, not just the breach (REC-05 does this for counts; delay needs the same)
* Event time and arrival time are different clocks (a source offline for an hour is not a platform breach)
* Simulated numbers must never be passed off as measured

## Considered Options

* A. Measure only end to end
* B. Every hop stamps its own time on the record or the batch; delay reported per hop and end to end; each number labelled measured or modeled
* C. Measure per hop only in benchmarks, not in production

## Decision Outcome

Chosen option: "B". Stamps, in order where they apply: event time, sender time, front-door time, file written, landing
seen, bronze, silver, gold window complete; for the live lane: processed, stored, pushed; for change capture: source
commit, change file written, then the platform hops. Rows carry the stamps they can (DPC-0022); batches carry the
rest in the run log. The report gives the 50th, 95th and 99th percentile per hop and end to end, a waterfall per path,
and both clocks (from event time and from arrival time), and names the hop that broke each breached promise. In the
simulator, hops we run are measured and hops we cannot run are modeled; every number carries that label.

### Consequences

* Good, because a breach points at its hop
* Good, because benchmark and production reports use the same stamps
* Bad, because a few more columns per row and per run record

### Confirmation

A world scenario delays one hop on day 6; the report shows the breach on day 6 and names that hop; modeled hops show
the label in the report.

## More Information

Ops tables: the per-minute stream table and the gold completeness table from the streaming design; batch stamps go
through the run recorder (ADR-024).
