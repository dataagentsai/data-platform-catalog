# DAC, the Data Assurance Catalog (v0.1, draft)

**What must be true of a data platform**, written so that each line can be tested, with no product names. It is the
data sibling of the [AI Assurance Catalog](https://github.com/dataagentsai/ai-assurance-catalog). DAC lives in
this folder until about 30 obligations are stable, and then moves to its own repository (PLAN.html).

- [INDEX.md](INDEX.md): every obligation in one table.
- [obligations/](obligations/): the normative records, one file per cross-cutting concern (X1 to X22).
- [triage.yaml](triage.yaml): which review checks became obligations, and why the others did not.

## Where it came from

DAC v0 was the 91 technical checks in
[data-project-review](https://github.com/dataagentsai/data-project-review) (`packs/tech`). Those checks were
already tested blind on a sample project and found 27 of 27 planted gaps. They are written as questions for a
reviewer reading a project's documents. DAC turns the ones a running platform can be tested for into
obligations, and keeps the same ids, so a review finding and a failing platform test point at the same thing.

| What happened to the 91 checks | Count | Why |
|---|---|---|
| Became an obligation (same id) | 54 | A running platform can be tested for it, for example "a file loaded twice changes no total" (DUP-01). |
| Stayed review-only | 37 | It is about a project's estimate, plan, handover or a business decision, for example estimation (EST-*) or choosing which number the business trusts (REC-02). Each one's reason is in `triage.yaml`. |
| New, no review check | 12 | Platform rules no contract format covers (REUSE.md section 3 and the rules R2 to R9 in PLAN.html): nothing passes by absence, a contract is never loosened to pass, agents propose and gates decide, data flows one way, every incident kind has a planted test, everything deployed was declared, concerns on by default, configuration fingerprint per run, reconciliation names the hop, lineage on every hop, profiling drift, self-healing through the same gates. |

That gives **66 obligations, 39 of them core** (core means every platform owes it, whatever its shape). PLAN.html
expected about 30 core; the extra nine are kept because each has a failure story from a real project behind it.
Trimming is a question for the v0.1 gate review (DE-027).

## The record

Adopted from AAC's record, with the review fields that proved useful kept.

```yaml
- id: DUP-01                 # permanent. Same id as the review check it came from, or a new prefix.
  status: draft              # draft | active | deprecated
  since: 0.1.0
  title: Same batch or file arriving twice
  concern: X15               # one of core/concerns.yaml; the file it lives in
  level: MUST                # MUST | SHOULD | MAY, and the statement uses that word
  core: true                 # owed by every platform, whatever its shape
  dimension: uniqueness      # ODCS 3.2.0 quality dimension, or null (see crosswalks/quality-dimensions.yaml)
  stages: [landing, bronze, silver, gold]   # from core/stages.yaml
  statement: A file or batch delivered a second time MUST NOT change ... # the normative sentence
  failure_mode: After an outage the source resent yesterday's file ... # the story of what goes wrong
  test: Load the same file twice in a test environment ...              # the test that discharges it
  evidence: A business key or file fingerprint ...                      # what a passing platform leaves behind
  cites:                     # cite, never restate. Standard ids in core/standards.yaml.
    - {standard: ODCS, ref: "quality[].metric = duplicateValues"}
    - {standard: DAMA-DMBOK, ref: "Data Quality, chapter 13"}
  review_check: DUP-01       # the data-project-review Tech check it came from, or null
  plan_rule: R7              # optional: the PLAN.html rule a new obligation comes from
  related: [DUP-02, REC-01]
```

Rules (checked by `scripts/lint.py`, tested by `tests/test_lint.py`):

- No product names in title, statement, failure_mode, test or evidence. Product names live only in bindings.
- Every cite names a standard listed in `core/standards.yaml` and gives a ref in that standard's ref style.
- The dimension is an ODCS word, not a DAMA or ISO word. The crosswalk maps between them.
- Every related id exists. Every record imported from a review check is listed in `triage.yaml`.

## Known gaps in v0.1

- DAMA chapter numbers come from the 2nd edition's contents and have not yet been checked on a copy
  (`verified: false` in `core/standards.yaml`). ISO/IEC 25012 is cited only by the seven names already confirmed.
- No obligation is yet linked to the DPC capability that discharges it. That comes with DPC (DE-020), and then the
  linter will check that every obligation is covered by a capability.
- Two obligations (SIM-01, HEAL-01) cite nothing, because nothing outside this family covers them.

## Commands

```bash
uv run scripts/lint.py                                   # lint the catalog
uv run scripts/index.py                                  # regenerate INDEX.md after editing records
uv run --with pytest --with pyyaml --with jsonschema pytest -q   # table-driven tests
```
