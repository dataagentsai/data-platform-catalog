---
id: ADR-018
status: accepted
date: 2026-11-04
decision-makers: [platform owner]
consulted: [session A (practices), deck reviewers]
concerns: [X9]
dpc: [DPC-0059]
dac: [SERV-02, PERF-02]
plan: [G2, G8]
source: ["ETL page completeness"]
---

# ADR-018 A gold window is complete only when every input has caught up

## Context and Problem Statement

A job that ran on time can still publish half a day. Completeness must be judged by the data, not the schedule.

## Decision Drivers

* No partial number shown as complete
* Quiet sources stay green; broken ones go red

## Considered Options

* Complete when the job finished
* Complete when every input's bookmark in source time is past the window's end

## Decision Outcome

Chosen option: "Complete when every input's bookmark in source time is past the window's end", because each input writes how far it has loaded in source time, even on empty runs; a window is complete only when all are past it; incomplete windows are flagged or held as the fact declares and revisited.

### Consequences

* Good, because dashboards say when a number is incomplete
* Good, because freshness is the bookmark, not the last run
* Bad, because every mover must report a bookmark, including quiet rules per source kind

### Confirmation

The tyre world delivers one input late; the oracle checks the window is flagged, then completed.

## More Information

Capabilities: DPC-0059. Obligations: SERV-02, PERF-02. Plan: G2, G8. Source: ETL page completeness.
