# The Data Spec Charter

**What a specification in the data family is, and where any given statement belongs.** Draft 0.1.0 (DE-025).

This is a pointer, not a second charter. The AI family's
[Spec Charter](https://github.com/dataagentsai/clean-ai-engineering/blob/main/SPEC-CHARTER.md) already settles
form: the register, the routing rule, the dependency invariant, conformance language, versioning, evidence, and
what is not a specification. All of it applies here unchanged. This page says only what the data family maps or
adds.

## 1 · The register, mapped

| Data family | Says | Scope | AI family twin | Where |
|---|---|---|---|---|
| **DAC**, Data Assurance Catalog | what must be **TRUE** | universal | AAC | `dac/` |
| **DPC**, Data Platform Catalog | what must **EXIST** (capabilities and ports) | universal | AHC | `dpc/` |
| **DWD**, Data World Description | what must be **FACED** | per platform or slice | AWD (DWD extends `awd/v0`) | `slices/*/world.yaml` |
| **DPM**, Data Platform Manifest | what this platform **DOES**, per dataset | per company | AOAS | `dpm/`, `slices/*/manifest/` |
| **DBS**, Data Binding Spec | **which product** fills each port | per stack (engine layer + cloud layer) | ABS (the harness profile format) | `dbs/engine/`, `dbs/cloud/`, `dbs/stacks/` |
| ADRs (not a spec) | **why** a design was chosen | per decision | the AI family's decision log | `adr/` |

Derived, generated and never hand-edited: the DAC index (`dac/INDEX.md`), the ADR index (`adr/README.md`),
coverage by concern per stack (`scripts/coverage.py`), and, at run time, the evidence view that joins every verdict for one run.

## 2 · The routing rule, for data

1. **Every platform, or this one?** A statement that names a business noun (order, customer, store) is per
   company: DPM or DWD. Otherwise a catalog.
2. **What kind of statement?** A property that must hold: DAC. A part or a plug: DPC. A source and the incidents it
   throws: DWD. How one dataset is loaded: DPM.
3. **Does it name a product?** Then it is DBS, however much it feels like design.
4. **Is it the reason for a choice** (the options weighed and why one won)? Then it is an ADR, and the DPC, DAC
   or practice text that carries it out cites the ADR id instead of repeating the argument.

## 3 · What the data family adds

- **Adopted standards are cited, never restated.** A table's columns, types and quality rules live in its ODCS
  contract; a DPM manifest points at the contract and pins its version. DAC cites ODCS by version and field path.
- **The manifest is metadata, not code.** Everything a pipeline needs is read from the metadata DB at run time;
  config keys must be registered (`dpm/keys.yaml`).
- **Every binding says what the platform covers and who fills the gap** (`coverage`, `gap`, `gap_filled_by`), so
  "use the platform first, build only the delta" is checkable.
- **Every verdict carries a run id**, so evidence for one number can be gathered in one place.

## 4 · Checked mechanically

`scripts/lint.py` enforces what can be enforced today: required fields, no product names outside bindings, cited
ids exist, manifests and bindings against their schemas, ports and obligations referenced by a binding exist.
The dependency invariant (bindings may name obligations; obligations never name a product) is the product-name
check plus the id checks.
