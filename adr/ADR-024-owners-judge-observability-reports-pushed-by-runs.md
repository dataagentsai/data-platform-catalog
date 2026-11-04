---
id: ADR-024
status: accepted
date: 2026-11-04
decision-makers: [platform owner]
consulted: [design discussion 4 Nov]
concerns: [X8, X9, X14, X7]
dpc: [DPC-0019, DPC-0020, DPC-0021, DPC-0056, DPC-0057, DPC-0058, DPC-0018, DPC-0078]
dac: [OPS-01, OPS-03, OPS-06, LATE-01]
plan: [G8, G13]
source: ["design discussion 4 Nov: observability, system tables, three customer levels"]
---

# ADR-024 Owners judge, observability reports; pushed by runs; platform telemetry adopted, our metadata added

## Context and Problem Statement

Health information comes from three places: the platform's own telemetry (job runs, lineage, audit, query history
in system tables), our run log (datasets, batches, watermarks, held batches, configuration), and the data expectation
services (quality, reconciliation, profiling, quarantine). Without a rule, the same check is judged twice, screens
duplicate each other, alerts arrive from several places, and polling jobs run every few minutes whether anything
happened or not. Some customers have only the platform's telemetry, some have their own run log, some use ours.

## Decision Drivers

* One verdict per check, one alert engine, no duplicate screens
* Cost follows events and use, not the clock
* Adopt what the platform already gives; build only what needs our metadata
* Works for a customer with no run log of ours
* Agents and conversation interfaces read certified definitions through tools

## Considered Options

* Observability judges everything (quality, reconciliation, freshness, runs) and polls every source on a schedule
* Each owner judges its own checks; observability collects, shows, alerts and explains; results are pushed by runs;
  platform telemetry is read daily or on demand

## Decision Outcome

Chosen option: "Each owner judges; observability reports", with these rules:

1. **Three sets, separate.** (a) Platform-native screens and notifications are adopted, not rebuilt (job monitoring
   template, job failure notifications, lineage and audit views). (b) Observability (ours) covers pipelines and runs:
   per-dataset and per-batch run health, freshness against the manifest's promised targets, held and duplicate
   deliveries with the reason, gold windows waiting on an input, configuration per run, business blast radius, the
   SLO report, alert routing and noise rules. (c) Data expectation services (ours) cover whether the data is right:
   quality results, reconciliation, profiling, quarantine and release. Observability never judges data content.
2. **One step format.** Ingestion, the data expectation services and the gold harness write one result row per check
   to the run log (`detect.*`, `quality.*`, `recon.*`, `profile.*`) with a severity. Observability reads only that row
   to alert and to mark a run passed, warned or blocked; details stay with the owner, and alerts link to the owner's
   screen. Fixes go to the owner's gate (for example, quarantine release goes through the release flow).
3. **One alert engine.** Owners record severities and never send alerts. Delivery uses the platform's notification
   channels; routing by tier and the noise rules (OPS-06) are ours.
4. **Push, not poll.** Runs record results and raise alerts as they finish. Lateness, which has no event, is checked
   against the run log in the metadata store (no engine compute). Platform telemetry is copied once a day with a
   watermark; anything newer is read on demand by a tool or a screen. No fixed-interval polling jobs.
5. **Declarative pipelines report themselves.** Where silver or gold runs as a declarative pipeline, per-table row
   counts and status come from the pipeline's event log, not a second record in our run log.
6. **Three customer levels, same screens and tools.** Platform telemetry only (no run log); the customer's own log
   connected through an adapter on the run-log port; or our framework. Columns that need a log stay empty until one
   is connected. The run log is always read through its port, never directly.
7. **Certified ops definitions.** Screens, conversation interfaces and agents read ops metric views over compact ops
   tables, never raw telemetry. Agents call typed tools (verified functions), never direct queries; the same
   functions serve as trusted answers for the conversation interface.
8. **Cost is out of scope.** Spend and billing belong to the separate cost product; we keep job tags (domain, data
   product, run id) so it can attribute spend.

### Consequences

* Good, because each check has one owner and one verdict, and each problem raises one alert
* Good, because nothing runs when nothing happens
* Good, because the platform's free screens are reused and our build is limited to what needs our metadata
* Good, because the same product serves customers with or without our run log
* Bad, because the step format is a contract every owner must keep; a contract test enforces it
* Bad, because platform telemetry newer than the daily copy costs a query each time it is asked for

### Confirmation

On the tyre world, each planted incident is judged by its owner, appears once on the right screen, raises exactly one
alert, and the triage agent explains it through tools; a contract test checks every owner's step rows; a test runs the
screens with no run log connected and checks they render the telemetry-only columns.

## More Information

Capabilities: DPC-0019, DPC-0020, DPC-0021, DPC-0056, DPC-0057, DPC-0058, DPC-0018, DPC-0078. Obligations: OPS-01,
OPS-03, OPS-06, LATE-01. Plan: G8, G13. Applies at the W3 merge and to W1e (data expectation services) and W4 (agents).
