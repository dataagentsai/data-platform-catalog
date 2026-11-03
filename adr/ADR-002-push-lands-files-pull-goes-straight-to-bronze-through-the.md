---
id: ADR-002
status: accepted
date: 2026-11-04
decision-makers: [platform owner]
consulted: [session A (practices), deck reviewers]
concerns: [X3, X15, X12]
dpc: [DPC-0037, DPC-0038, DPC-0023, DPC-0070]
dac: [SCH-02, SEC-01, DUP-01, ING-01, RAW-01]
plan: [D11, G2]
source: ["ETL page principle 1", "deck big picture: pull, no landing"]
---

# ADR-002 Push lands files; pull goes straight to bronze through the lander steps

## Context and Problem Statement

Data reaches the platform two ways. Push: something at the source writes files (a change-capture service, a transfer service, a partner). Pull: our own reader connects to the source. Slice 1 sent everything through landing. Copying pulled data to landing only to read it back costs a hop and adds nothing, but skipping landing must not skip the checks.

## Decision Drivers

* Every batch must pass the same checks (contract, personal data, mass delete, batch log)
* No needless copies of personal data
* A replay must still be possible

## Considered Options

* Everything through landing
* Push through landing; pull runs the lander steps in-process to bronze
* Managed connectors writing straight into tables

## Decision Outcome

Chosen option: "Push through landing; pull runs the lander steps in-process to bronze", because the checks are a library, not a place: the puller calls the same lander steps the file lander calls, so pull gets every check without a second copy, and bronze (append-only, as delivered) is the replay point for both.

### Consequences

* Good, because one set of entry checks for every batch source
* Good, because no landing copy of pulled personal data
* Good, because bronze is the replay point for push and pull alike
* Bad, because managed connectors that write straight into tables are not used until they can call the lander steps
* Bad, because streams are the stated exception: the stream bus is their landing and the streaming reader their lander

### Confirmation

A static check that every code path writing bronze goes through the lander steps; the tyre world's pull sources plant a schema change and a mass delete that must be caught with no landing copy.

## More Information

Capabilities: DPC-0037, DPC-0038, DPC-0023, DPC-0070. Obligations: SCH-02, SEC-01, DUP-01, ING-01, RAW-01. Plan: D11, G2. Source: ETL page principle 1; deck big picture: pull, no landing.
