# Layers: the hard challenges of each layer and hop, and how we solve them

One record per layer or hop of the data flow, in order: source, ingestion, bronze, bronze to silver, silver, silver
to gold, gold, gold to semantic, semantic, semantic to experiences. Each says what the layer must achieve, its hard
challenges (what goes wrong, a tyre-world example, how we solve it, a verdict and a status, with links to DAC
obligations, ADRs and practices), and its common anti-patterns (reused from `practices/` by id where one fits).

The client deck and the cleandataengineering.ai pages are generated from these files, so they always agree.

| Field | Values |
|---|---|
| `verdict` | `solve` (once declared, the engine does it and a test proves it) · `assist` (the tool suggests, warns and tests; a person confirms) · `people_decide` (a business decision the tool records, versions and enforces) |
| `status` | `built` · `building` · `designed` · `gap` |
| `world_day` | the day of the 14-day tyre world whose planted incident tests it |
| `components` | contracts, metadata_store, puller, lander, silver_engine, gold_harness, des, semantic_generators, observability, agents, app |

No product names in normative text (rule R1). Checked by `scripts/lint_layers.py`, tested by `tests/test_layers.py`.

```bash
uv run scripts/lint_layers.py
```
