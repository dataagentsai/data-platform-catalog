---
id: ADR-028
status: accepted
date: 2026-11-12
decision-makers: [platform owner]
consulted: [tyre client brief, a published airline reference case]
concerns: [X13, X11, X7]
dpc: [DPC-0089, DPC-0066, DPC-0075, DPC-0006]
dac: [SEC-02, SEC-04, LIN-01]
plan: [16d, F2, B12]
source: ["12 Nov session: who owns the catalog, the engine's or the cloud's; how two catalogs stay in step"]
---

# ADR-028 One catalog of record; other engines federate over an open catalog protocol; governance is compiled into each

## Context and Problem Statement

The client's cloud has its own catalog and query engines; the engine has its own catalog with lineage, masks,
certified metrics and conversation interfaces. Both want to "own" the tables. Two catalogs that copy or sync each
other drift; one engine writing tables another catalog owns loses governance. What is the clean shape, and what does
"open" have to mean so a client can leave?

## Decision Drivers

* One answer to "which version is current", always
* No copies and no sync jobs
* Lineage, masks and certified metrics must keep working for the engine's users
* The cloud's engines must read the same tables, with permissions enforced
* "Open" must be provable: the tables must be readable after the vendor is gone

## Considered Options

* A. The cloud's catalog owns the tables; the engine reads them through federation (read-only) or writes them outside its own governance
* B. The engine's catalog owns the tables; the cloud's catalog federates to it over the open catalog protocol and reads live; permissions compiled into both from one manifest
* C. Both catalogs hold their own registration, kept in step by a sync job

## Decision Outcome

Chosen option: "B", because it keeps one writer and one catalog of record, needs no copy, and is the pattern a large
published reference case runs in production. The rules:

1. **One writer per table** (DPC-0006): the engine writes; the cloud's engines read.
2. **One catalog of record**; every other catalog **federates** over the open catalog protocol and reads the current version at query time. Nothing is copied, so nothing is synced.
3. **Tables in an open table format, in the client's own storage account** (ADR-027).
4. **Governance as code, compiled into each catalog**: the access model (DPC-0066) generates the grants for the catalog of record and for the federating catalog from one manifest, and a nightly drift check compares them, because permissions, masks, tags and lineage do not cross a federation boundary.
5. Restricted columns are either kept out of what the federating catalog can see or shown only through a masked view.
6. **An exit drill**, run as a test: register the same tables in a second catalog and read them with no engine of ours running.

A remains a separate proof-of-concept realm (its own binding and branch), built only if a client chooses it. C is
dropped.

### Consequences

* Good, because no sync job to fail and no lag beyond the format's own commit
* Good, because the client's existing query engines keep working during a migration, reading the new tables
* Good, because "open" is a passing test, not a claim
* Bad, because two permission systems exist; the generator and the drift check are ours to keep
* Bad, because the cloud's engines read only; any write from them goes through the engine

### Confirmation

The access generator produces both grant sets from the tyre manifest; the drift check fails when one grant is removed
by hand. The exit drill registers bronze, silver and gold in a second catalog and the known answers read back equal.

## More Information

Products for each role are named in the engine binding (`dbs/engine/`) (`data_catalog`, `access_control`) and
the cloud binding (`dbs/cloud/`) (`federated_catalog`). The other-catalog-owns realm is TODO 16d's proof-of-concept realm.
