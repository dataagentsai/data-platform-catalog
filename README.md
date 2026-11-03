# Data Platform Catalog

**What a data platform must have** (capabilities, by spine stage and cross-cutting concern), written with no
product names, the data sibling of the [AI Harness Catalog](https://github.com/dataagentsai/ai-harness-catalog).
Part of [Clean Data Engineering](https://cleandataengineering.ai/).

## What is here today

| Part | What it says | Status |
|---|---|---|
| [dac/](dac/) | DAC, the Data Assurance Catalog: what must be **true** of a platform, as testable obligations, each naming how it is enforced | v0.1 draft: 84 obligations, lint-clean |
| [practices/](practices/) | How we meet each obligation: principles, practices and anti-patterns, each linked to DAC. The engineering best-practices page is generated from here | v0.1 draft: 132 practices |
| [core/](core/) | Shared vocabulary: the 22 cross-cutting concerns, the spine stages, the ten pipeline archetypes, the standards we cite | v0.1 draft |
| [crosswalks/](crosswalks/) | Mappings to outside vocabularies (quality dimensions: ODCS, DAMA, ISO/IEC 25012) | v0.1 draft |
| [dpc/](dpc/) | DPC, the Data Platform Catalog: what must **exist**. 22 ports and 32 capabilities (slice 1) | v0.1 draft, in progress |
| [slices/01-orders/](slices/01-orders/) | Slice 1, orders source to silver: contract, manifest, world with 4 incidents, Databricks binding | spec draft, cross-checked |

DAC starts from the tested technical checks in
[data-project-review](https://github.com/dataagentsai/data-project-review) and keeps their ids.

## Commands

```bash
uv run scripts/lint.py
uv run scripts/lint_practices.py              # practices and enforced_by (reads ../shift-left-bundle)
uv run scripts/build_practices_page.py        # regenerate the best-practices page
uv run --with pytest --with pyyaml --with jsonschema pytest -q
```

Licence: specification text CC BY 4.0.
