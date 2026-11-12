---
id: ADR-029
status: accepted
date: 2026-11-12
decision-makers: [platform owner]
consulted: []
concerns: [X15, X12, X18]
dpc: [DPC-0023, DPC-0028, DPC-0071, DPC-0095]
dac: [HIST-04, RAW-01, SEC-03, REL-07]
plan: [16e, B8]
source: ["12 Nov session: how much bronze keeps, retention, and the reload paths: from source, from landing, from landing archive"]
---

# ADR-029 Reload from the nearest correct copy; retention is set per dataset and never breaks a rebuild

## Context and Problem Statement

A fault can enter at the source, at the mover, at the lander, or after bronze. Each needs a different reload: from
the source, from landing, from an archive of landing, or from bronze. Retention decides which copies still exist when
a fault is found months later. Bronze kept forever is safe for replay but grows without end; landing holds personal
data that is not yet tokenised. How much does each layer keep, and which copy does a reload read?

## Decision Drivers

* Most faults are found after the copy they need has aged out, unless retention is planned for it
* A whole-table history rebuild from bronze must stay complete even after old bronze is deleted
* Landing holds personal data in clear; bronze holds tokens (DPC-0070)
* Never reload from the source when a nearer correct copy exists: it loads the source and the source may have changed
* Every reload is an ordinary, logged run (ADR-025)

## Considered Options

* A. Keep everything forever in every layer
* B. Reload always from the source
* C. Reload from the nearest correct copy, chosen by where the fault entered; retention per layer and per dataset in metadata; a baseline batch before bronze ages out

## Decision Outcome

Chosen option: "C".

| Fault entered | Example | Reload from |
|---|---|---|
| After bronze (silver or gold logic, a rule, history) | a wrong cast in silver | bronze (ADR-025: void, rebuild silver, rerun gold windows) |
| At the lander, found early | a date misread for two weeks | landing, hot |
| At the lander, found late | the same, found after four months | landing archive, restored |
| At the mover or the source | missing deliveries, a source correction | the source (a new full load) |

Retention, as settings per dataset with these defaults: landing hot 30 days; landing archive as long as bronze for
datasets with no personal data, 90 days for datasets with personal data; bronze 3 years in standard storage then a
cheaper storage class that stays readable; table version history (time travel) 7 to 30 days, for undo only. **Bronze
is append-only and keeps every delivery as delivered**, duplicates included; it is never cut to "latest rows". Before
the oldest bronze ages out, the platform writes a **baseline batch**: silver's state as of the cut-off, written into
bronze as a marked batch, so a rebuild is the baseline plus every later batch. Small reference tables may keep bronze
forever instead. Erasure of a person deletes their token-vault entry; bronze keeps only tokens.

### Consequences

* Good, because a fault found late still has a correct copy to reload from
* Good, because full history rebuilds stay complete after deletion
* Good, because personal data in clear lives at most 90 days in an archive
* Bad, because the baseline batch is a new kind of batch the lander and history stage must recognise
* Bad, because a lander fault found after 90 days on a personal-data dataset can only be fixed from the source

### Confirmation

World scenarios: a lander fault planted on day 3 and found on day 12 reloads from the landing archive and gold equals
the oracle; a rebuild after bronze before day 5 is deleted, from the baseline plus days 5 to 14, gives the same silver;
a personal-data landing file older than its limit is gone and the run log shows the deletion.

## More Information

Extends ADR-025 (void and rerun). Settings: `landing_hot_days`, `landing_archive_days`, `bronze_retention_days`,
`bronze_baseline`, `version_history_days` (registered in the settings registry, B5).
