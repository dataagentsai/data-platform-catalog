# Practices: how we meet each "must be true" (v0.1, draft)

DAC says **what must be true** of a data platform. A practice says **how we meet it**: a principle every layer
follows, a practice in one place, or an anti-pattern we block. Every practice names the DAC obligations it serves,
and how it is enforced. The engineering best-practices page is **generated** from these files (decision D12); it is
never edited by hand.

One list per kind (goal G1):

| Kind | Lives in | Says |
|---|---|---|
| Obligation | [../dac/obligations/](../dac/obligations/) | What must be true, and (`enforced_by`) which checks, tests and reviews enforce it |
| Practice | here, one file per component | How we meet it, with a binding example |
| Static check | the shift-left bundle, `catalog/checks/*.yaml` | What is caught before anything runs; its `dac:` names the obligations |
| Proposed check | [proposed-checks.yaml](proposed-checks.yaml) | A static check the practices need that the bundle does not have yet |

## Files

- `canon.yaml` holds the principles. Every other file is one component from [components.yaml](components.yaml),
  and a practice lives in the file of its first component.
- [dropped.yaml](dropped.yaml): cards from the old page that were not kept, each with the reason. Ids are never reused.
- [proposed-checks.yaml](proposed-checks.yaml): delete an entry once the bundle ships that check. The linter fails
  while an id is in both places.

## The record

```yaml
- id: BP-090                 # permanent. Never reused, even after a drop.
  status: draft              # draft | active | deprecated
  since: 0.1.0
  kind: anti-pattern         # principle | practice | anti-pattern
  title: Appending to gold facts          # normative: no product names (rule R1)
  why: Every retry or late file double-counts.          # normative: no product names
  how:                       # a binding example. Product names belong here, and only here.
    binding: aws-databricks
    text: The harness writes with `replaceWhere` or MERGE only.
  instead: Replace the whole window, or MERGE on the grain key.   # anti-patterns only; normative
  layers: [gold]             # from core/stages.yaml (platform = cross-cutting)
  components: [s2g]          # from components.yaml; the first decides the file and the page section
  enforced_by:               # how this practice is enforced, in the order the page shows it
  - shift_left: [SL-CLEAN-31]           # checks in the shift-left bundle
  - proposed: SL-GOLD-01                # a check in proposed-checks.yaml
  - runtime: The orphan rate is checked before publish.   # a check on real data (binding text allowed)
  - review: Review of the join conditions.                # human judgement (binding text allowed)
  dac: [GOLD-01]             # required: at least one DAC obligation this practice serves
  adr: [ADR-006]             # optional: the design decisions behind it
```

Rules (checked by `scripts/lint_practices.py`, tested by `tests/test_practices.py`):

- Every practice serves at least one DAC obligation, and every id it names exists: DAC ids, shift-left check ids,
  proposed check ids, ADR ids.
- No product names in `title`, `why` or `instead`. The list is `lint.py`'s plus the AWS and Databricks names the
  page uses.
- An anti-pattern has `instead`; nothing else does. A principle lives in `canon.yaml`.
- Every proposed check is used by a practice, names DAC ids, and is not yet in the bundle.
- Every DAC obligation has an up-to-date `enforced_by` (see [../dac/README.md](../dac/README.md)), and one with no
  build-time check says so in `gap`.

The linter also prints notes, not errors: a practice that cites a check whose DAC links it does not share, and DAC
obligations no practice serves yet. A note that is intended goes in [accepted-notes.yaml](accepted-notes.yaml) with
its reason, and is then not printed; an entry whose note no longer fires is an error, so the list stays current. A
reason that starts "Bundle:" means the real fix is a `dac:` link on the shift-left bundle's check.

## The page

Each card shows the DAC obligations it serves and, when it has `adr:`, the decisions behind it ("Decided in", with
each ADR's title and a link to its file). An **ADR** badge marks those cards, and the "Decision record" filter
(`#adr=backed` or `#adr=none`) shows the cards with or without a recorded decision.

The page names no client unless a setting says so: `--client NAME` with `--out FILE`, or `client:` on a target in
`page-targets.local.yaml` at the repository root (not committed; copy
[../page-targets.example.yaml](../page-targets.example.yaml)). The template and the catalog never hold a client name.

## ADR ids

`adr:` names design decisions in [../adr/](../adr/), written by session B. The linter checks each id against the
files there. (Before that folder existed, the practices used ADR-001 to ADR-015 as placeholders in the order of
session B's brief; the ADRs it wrote kept those numbers.)

## Where it came from

The 134 cards of `~/Engineering-Best-Practices.html` (the AWS and Databricks client deck's page), imported once by
`scripts/import_practices.py` on 4 Nov 2026: 132 kept, 2 dropped. 18 DAC obligations were added for deck decisions
no obligation covered (`origin: deck` on those records). Titles that named products were reworded; the product
detail stays in `how`.

## Commands

```bash
uv run scripts/lint_practices.py          # lint practices and enforced_by
uv run scripts/enforced_by.py             # refresh enforced_by after the bundle or proposed-checks.yaml changes
uv run scripts/index.py                   # refresh dac/INDEX.md
uv run scripts/build_practices_page.py    # write the page to each target in page-targets.local.yaml (default ~/); --check to compare
uv run scripts/build_practices_page.py --out FILE --client "Name"   # one copy, naming a client
```

The shift-left bundle is read from `$SHIFT_LEFT_BUNDLE`, or `../shift-left-bundle` next to this repository.
