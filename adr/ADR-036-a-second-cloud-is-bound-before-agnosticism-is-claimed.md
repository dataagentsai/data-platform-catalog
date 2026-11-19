---
id: ADR-036
status: proposed
date: 2026-11-19
decision-makers: [platform owner]
consulted: [session A (practices), the explainer's code-map review]
concerns: [X16, X1, X11, X17]
dpc: [DPC-0088, DPC-0029]
dac: [REL-06, ORCH-05, REL-05, DUP-02]
plan: [M1, G3]
source: ["ADR-014 consequence: a new cloud is one cloud file plus adapters", "owner's question, 19 Nov 2026: how is it platform agnostic"]
---

# ADR-036 A second cloud is bound before agnosticism is claimed

## Context and Problem Statement

ADR-014 says a new cloud is one cloud file plus adapters, and ADR-015 keeps products out of the kernel. Both are claims.
Only one cloud has been bound, so nothing has shown that the ports, the engine layer, the settings dictionary and the
contract tables are free of that cloud's shape. A design is agnostic when binding a second cloud changes nothing in the
kernel, and until that is tried it is a promise.

## Decision Drivers

* Evidence, not a claim: the test of agnosticism is a second binding
* Specifications that tell the truth: every place the first cloud leaked into a spec is found and fixed there
* No cost before it is needed: the work starts with the specification and with adapters tested against fakes
* Honest status: nothing is called proven that has not run on a real account

## Considered Options

* A. Call the design agnostic without a second binding
* B. Bind a second cloud under the same engine, specification first, then adapters, then a real account
* C. Bind a second engine first
* D. Bind two more clouds at once

## Decision Outcome

Chosen option: "B", because it changes one half of the two-layer binding (ADR-014) and keeps the other still, so any change
it forces in the kernel, the ports or the engine layer is a real finding about agnosticism. The rules of the exercise:

* The cloud layer file is written first. Its `adapter` text says what is built and what is not, and `proves` lists only the
  obligations a test in the platform repository names.
* A cloud adapter passes the port's existing contract table. A row is added to the table; the table is not forked (ADR-020).
* Anything in the kernel, a port, the engine layer or the settings dictionary that turns out to be shaped for the first
  cloud is fixed there, never worked around in the adapter, and is listed under Consequences.
* Until the 3-day compressed run has passed on a real account of the second cloud, this record stays `proposed` and the
  cloud's stack says so.

### Consequences

* Good, because every claim of agnosticism becomes a thing that was tried
* Good, because the findings below are fixed in the specifications, where the next cloud would otherwise meet them again
* Bad, because the adapters can only be tested against a fake of the cloud's SDK surface until a real account exists, so
  they prove the adapter's own logic and not the cloud's behaviour
* Restriction: a real account run needs a paid subscription for the engine (owner decision D10); until then the stack's
  `accepted_gaps` list what has not been shown

**Findings from the first pass (19 Nov 2026), each fixed or recorded where it belongs:**

| # | What was shaped for the first cloud | Where | Action |
|---|---|---|---|
| F1 | The engine layer file named the first cloud's products in two decisions (the federated catalog, the metadata store's rationale) | the engine layer file in `dbs/engine/` | Fixed: the engine file now names no cloud; the federation decision belongs to each cloud file |
| F2 | The secret reference grammar allowed characters only the first cloud's secret store can hold | `secret_store` port, `cloud_ports.secret_name` | Fixed: the portable subset (letters, digits, hyphen, slash as a separator, no double hyphen, no hyphen beside a slash so the mapping stays reversible); the port text says so. The 127-character limit applies after the mapping and is checked by the adapter |
| F3 | The object store port spec listed `location` only, though its invariant and the code rely on `versioned`; the stream port spec lacked `shards` | `dpc/ports.yaml` | Fixed: operations added |
| F4 | The landing port spec named an operation `list`, the code and every adapter call it `deliveries` | `dpc/ports.yaml` | Fixed: renamed, intent corrected |
| F5 | Nine platform-scope settings in the dictionary are named for the older pipeline-tool design (a vault address, an integration-runtime name, a linked-service name, a function address, a storage account, a container, a lifecycle threshold, a metadata server, a batch count); three more name the engine's flattening notebook. The platform reads none of them | settings dictionary, `meta/settings_registry.json`, `dpm/keys.yaml` | Recorded, not fixed: removing them needs the older realm retired; tracked in the TODO |
| F6 | Versioning of the object store may not exist for the second cloud's data-lake storage type, and it is an account setting the data-plane client cannot read | `object_store` binding | Recorded in the binding as a partial coverage with its gap; recovery rests on the platform's own retention and table history (ADR-029) |
| F7 | The second cloud's managed change capture covers fewer database engines and is in preview | `mover` binding | Recorded as partial coverage; the gap is filled by an open-source log reader that is not yet validated |
| F8 | The second cloud's stream capture writes a row format the lander cannot read; the registry allows file formats the lander cannot read either | `stream_bus` binding, settings dictionary | Streams are read from partitions, never from capture output; the registry-versus-parser mismatch is tracked in the TODO |
| F9 | No port reports a stream's retention, so the retention invariant (ORCH-06) can only be a binding setting | `stream_bus` port | Recorded; the optional `retention` operation has no adapter yet |

### Confirmation

The DBS linter accepts the new cloud layer and stack, and the generated coverage file for the stack is current. The shared
contract tables for landing, the file drop, the object store and the secret store each carry a row for the new cloud's
adapter. The decision becomes `accepted` when the 3-day compressed run passes on a real account of the second cloud with
no change to the kernel; any change it forces is added to the findings first.

## More Information

Capabilities: DPC-0088, DPC-0029. Obligations: REL-06, ORCH-05, REL-05, DUP-02. Plan: M1, G3. The cloud layer and stack are
in `dbs/cloud/` and `dbs/stacks/`; the facts they rest on, with the date each was checked, are in the cloud file's header.
