---
id: ADR-030
status: accepted
date: 2026-11-12
decision-makers: [platform owner]
consulted: [tyre client brief]
concerns: [X1, X19, X22]
dpc: [DPC-0001, DPC-0035, DPC-0093]
dac: [CFG-01, SIM-01]
plan: [16f, B14]
source: ["12 Nov session, user: a lane can have more than one golden path; golden paths are benchmarked and selected"]
---

# ADR-030 A lane may have several golden paths; each is built behind ports, benchmarked, and chosen per dataset

## Context and Problem Statement

Every way of moving data into the platform has many product options. Supporting all of them is unbounded work;
forcing exactly one per lane ignores real differences (a client with a stream upstream, a client with only files, a
client that must run without our engine). How many routes do we build, and how is one picked?

## Decision Drivers

* Each route we offer must be fully built and tested end to end, not "supported in theory"
* A route must be picked by evidence for a given client and dataset, not by habit
* Adding a route must not change the stages or the metadata store
* The comparison itself is a deliverable a client can read

## Considered Options

* A. Exactly one golden path per lane
* B. A short list of golden paths per lane, built behind the same ports, benchmarked on the simulated world, chosen per dataset by the setting `lane_path`
* C. Support every product option on request

## Decision Outcome

Chosen option: "B". A golden path is a named set of adapters and a binding profile. Each one passes the port contract
tables (DPC-0093), runs the full world with every planted incident (SIM-01), and is scored on: delay end to end and
per hop (ADR-034), cost at demo and production scale, correctness against the oracle, recovery time, table health and
upkeep, parts to operate, openness (the exit drill, ADR-028), and governance coverage. One axis varies per comparison:
the path, the table format, or the compute. The binding sets the default path; `lane_path` overrides it per dataset.
Options not on the list stay documented with their reason, not built.

### Consequences

* Good, because each offered route has evidence behind it
* Good, because a client's choice is one setting, not a project
* Bad, because every golden path is code and tests we keep
* Bad, because benchmark numbers for routes we cannot run locally need a real cloud run; until then they are labelled modeled

### Confirmation

The benchmark report lists every golden path with all measures, labelled measured or modeled, and the world's known
answers equal on every path.

## More Information

Candidate list and round 1 in TODO 16f and the streaming design page; batch golden paths: files from landing (P1) and
a pull mover in front of landing (ADR-033).
