# Data Platform Catalog

**What a data platform must have** (capabilities, by spine stage and cross-cutting concern), written with no
product names, the data sibling of the [AI Harness Catalog](https://github.com/dataagentsai/ai-harness-catalog).
Part of [Clean Data Engineering](https://cleandataengineering.ai/).

## What is here today

| Part | What it says | Status |
|---|---|---|
| [dac/](dac/) | DAC, the Data Assurance Catalog: what must be **true** of a platform, as testable obligations, each naming how it is enforced | v0.1 draft: 89 obligations, lint-clean |
| [practices/](practices/) | How we meet each obligation: principles, practices and anti-patterns, each linked to DAC. The engineering best-practices page is generated from here | v0.1 draft: 132 practices |
| [layers/](layers/) | The hard challenges and common anti-patterns of each layer and hop (source to experiences), how we solve each, with a verdict and status; the deck and site pages are generated from here | v0.1 draft: 10 layers, 69 challenges, 37 anti-patterns |
| [core/](core/) | Shared vocabulary: the 22 cross-cutting concerns, the spine stages, the ten pipeline archetypes, the standards we cite | v0.1 draft |
| [adr/](adr/) | ADRs: **why** the platform is shaped as it is, one decision record each (MADR), cited by DPC, DAC and practices | 23 accepted |
| [crosswalks/](crosswalks/) | Mappings to outside vocabularies (quality dimensions: ODCS, DAMA, ISO/IEC 25012) and the client deck's 68 concerns to DPC (`deck.yaml`) | v0.2 draft: all 68 mapped |
| [dpc/](dpc/) | DPC, the Data Platform Catalog: what must **exist**. 44 ports and 102 capabilities; every DAC obligation discharged | v0.2 draft |
| [dpm/](dpm/) | DPM, the Data Platform Manifest: what one company **does**: datasets, gold tables, metrics, models, platform settings | v0.2 schemas |
| [dbs/](dbs/) | DBS, the Data Binding Spec: **which product** fills each port, as an engine layer plus a cloud layer composed by stacks | v0.2: Databricks engine (with a Free Edition profile), AWS cloud, 2 stacks |
| [slices/01-orders/](slices/01-orders/) | Slice 1, shop orders source to silver: contract, manifest, world with 4 incidents | spec draft, built and run |
| [slices/02-tyre/](slices/02-tyre/) | Slice 2, the tyre company: 15 contracts, 20 manifests (datasets, gold, metrics, a model, platform), a 14-day world with 11 incidents | spec draft, cross-checked |

DAC starts from the tested technical checks in
[data-project-review](https://github.com/dataagentsai/data-project-review) and keeps their ids.

## Commands

```bash
uv run scripts/lint.py
uv run scripts/lint_practices.py              # practices and enforced_by (reads ../shift-left-bundle)
uv run scripts/lint_layers.py                 # layers: challenges and anti-patterns per layer and hop
uv run scripts/build_practices_page.py        # regenerate the best-practices page (targets: page-targets.local.yaml)
uv run --with pytest --with pyyaml --with jsonschema pytest -q
```

Licence: specification text CC BY 4.0.
