---
id: ADR-035
status: accepted
date: 2026-11-13
decision-makers: [platform owner]
consulted: [13 Nov session on declarative pipelines]
concerns: [X1, X15, X17]
dpc: [DPC-0115]
dac: [ENG-02, ENG-01, PURE-01]
plan: [D6, B16]
source: ["13 Nov session, user: support both, people ask for declarative these days; set the bronze-to-silver engine somewhere and support both golden paths"]
---

# ADR-035 Two bronze-to-silver engines behind one port, chosen per dataset

## Context and Problem Statement

ADR-026 runs silver as our own thirteen stages and our own history write on job compute, and dropped the engine's
declarative pipeline. Clients now ask for declarative pipelines, an open-source declarative engine has appeared (the
binding names it), and on serverless compute a declarative pipeline costs the same as a job. Do we offer one way to
run bronze to silver, or both, and how is one picked without two copies of the logic?

## Decision Drivers

* Clients ask for declarative pipelines; the platform should not refuse a common, reasonable choice
* One copy of the transformation logic: the thirteen stages must not be rewritten per engine (PURE-01)
* Gold and every consumer must not know or care which engine built silver
* Each engine offered must be fully built and proven, not "supported in theory" (ADR-030)
* Per-batch recovery (ADR-025) and the extra history kinds (ADR-032) must not be lost silently

## Considered Options

* A. Keep one engine: our job path only (ADR-026 as it stands)
* B. Replace it with the declarative engine
* C. Both, behind one stage-runner port, chosen per dataset by the setting `silver_engine` (`job` | `declarative`)

## Decision Outcome

Chosen option: "C", because it follows ADR-030 (several golden paths per lane, chosen per dataset) and keeps one copy
of the logic. Both engines:

* read the same manifests and contracts, call the same thirteen stage functions, and write the same silver tables
  through the table port, so gold is unchanged;
* write the same run log, so operations screens look the same;
* pass one contract test table for the stage runner and the compressed simulated world (every planted incident)
  against the oracle, in continuous integration.

The declarative engine declares one streaming table per dataset from the metadata (a loop over manifests, never a
file per dataset). Its history comes from the engine's managed change capture (SCD Type 1 or 2) where available; the
stages run inside the flow as plain functions. A dataset whose settings the declarative engine cannot honour (snapshot
or source-versioned history, a feature missing in the bound product) is refused by the manifest loader with the
reason, never silently run another way.

`job` stays the default until the declarative engine passes the proof; `declarative` is opt-in per dataset.

### Consequences

* Good, because clients who want declarative get it without a second set of transformations
* Good, because the open-source declarative engine keeps the path portable; the vendor's version adds its own features as a binding
* Good, because the comparison (correctness, recovery, cost, lines we own) is evidence, not habit
* Bad, because two shells to keep working and a second world run in continuous integration (about two minutes)
* Bad, because per-batch void and rebuild is weaker on the declarative engine (a full refresh, or the rebuild run on the job engine)
* Neutral: quarantine with reasons stays ours on both; the vendor's quality rules may feed it, never replace it

### Confirmation

Both engines pass the stage-runner contract table and give silver equal to the oracle on the compressed calendar.
The manifest loader refuses a `declarative` dataset that asks for an unsupported history kind. The feature matrix of
the two engines is generated from the binding and published with the comparison.

## More Information

Amends ADR-026 (which stays accepted for the `job` engine). Product names, editions and the open-source question
about managed change capture live in the engine binding (`dbs/engine/`). First build: the spike of 13 Nov (one
dataset through the open-source declarative engine on the default table format (ADR-027), compressed world), then all datasets.

Spike step 1 (13 Nov 2026): the open-source declarative engine's managed change capture keeps SCD Type 2 history only in an engine version that no open table format supports yet (details in the binding and in the framework's spikes/sdp_silver). Until then the declarative engine binds to the vendor's product; the open-source binding is rerun when a format catches up.
