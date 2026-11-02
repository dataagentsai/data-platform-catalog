# Data Platform Catalog

**What a data platform must have** (capabilities, by spine stage and cross-cutting concern), written with no
product names, the data sibling of the [AI Harness Catalog](https://github.com/dataagentsai/ai-harness-catalog).
Part of [Clean Data Engineering](https://cleandataengineering.ai/).

## What is here today

| Part | What it says | Status |
|---|---|---|
| [dac/](dac/) | DAC, the Data Assurance Catalog: what must be **true** of a platform, as testable obligations | v0.1 draft: 66 obligations, lint-clean |
| [core/](core/) | Shared vocabulary: the 22 cross-cutting concerns, the spine stages, the standards we cite | v0.1 draft |
| [crosswalks/](crosswalks/) | Mappings to outside vocabularies (quality dimensions: ODCS, DAMA, ISO/IEC 25012) | v0.1 draft |
| DPC capabilities | What must **exist**: each stage of the spine and each concern as capabilities with ports | Next |

DAC starts from the tested technical checks in
[data-project-review](https://github.com/dataagentsai/data-project-review) and keeps their ids.

## Commands

```bash
uv run scripts/lint.py
uv run --with pytest --with pyyaml pytest -q
```

Licence: specification text CC BY 4.0.
