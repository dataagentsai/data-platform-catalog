"""DPM v0.2 checks (D15): the new dataset blocks and the gold, metric, ML model and platform kinds.
Each row breaks one tyre manifest in one way and names the error expected."""
import copy
import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import lint  # noqa: E402
import lint_shape as ls  # noqa: E402

ROOT = lint.ROOT
D = ROOT / "slices" / "02-tyre"
DOM = ls.load_domain(D)
PLATFORM = DOM["platform"][1]
SD = ROOT / "dpm" / "schema"
V = {k: ls._validator(SD, f"{k}.schema.json") for k in ("dataset", "gold", "metric", "ml_model", "platform")}
DS_COLS = {k: ls.contract_columns(yaml.safe_load((f.parent / m["contract"]).read_text())) for k, (f, m) in DOM["dataset"].items()}
DIMS = {n for n, (_, g) in DOM["gold"].items() if g["kind"] == "gold_dimension"}
FACTS = {n for n, (_, g) in DOM["gold"].items() if g["kind"] == "gold_fact"}
GOLD_COLS = {n: ls.contract_columns(yaml.safe_load((f.parent / g["contract"]).read_text())) for n, (f, g) in DOM["gold"].items()}


def put(doc, path, value):
    d = copy.deepcopy(doc)
    *parents, last = path.split(".")
    node = d
    for p in parents:
        node = node[int(p)] if isinstance(node, list) else node[p]
    if value is DEL:
        del node[last]
    else:
        node[last] = value
    return d


DEL = object()


def dataset_errors(key, path, value):
    f, m = DOM["dataset"][key]
    c = yaml.safe_load((f.parent / m["contract"]).read_text())
    m2 = m if path is None else put(m, path, value)
    errs = ls._schema_errors(V["dataset"], m2, key)
    return errs or ls.lint_dataset_v02(m2, c, PLATFORM, key)


DATASET_CASES = [
    ("pull full copy valid", "erp.material", None, None, None),
    ("push change feed valid", "erp.sales_order_line", None, None, None),
    ("unknown dataset kind", "erp.material", "kind", "table", "was expected"),
    ("unknown history kind", "erp.material", "history.kind", "lookup", "is not one of"),
    ("history type does not fit the load", "erp.material", "load.pattern", "append", "history scd2 does not fit"),
    ("tracked column not in contract", "erp.material", "history.track_columns", ["colour"], "'colour', which is not"),
    ("tracked columns on an append dataset", "mes.production", "history.track_columns", ["tyres_cured"],
     "track_columns only applies to history scd2"),
    ("pull through landing", "erp.material", "reconciliation.hops", ["sources", "landing", "bronze", "silver"],
     "no landing hop (ADR-002)"),
    ("stream through landing", "press_stream.press_reading", "reconciliation.hops", ["sources", "landing", "bronze"],
     "no landing hop"),
    ("ingest mode against archetype", "press_stream.press_reading", "archetypes", ["PA1"], "ingest stream needs"),
    ("full copy without delete detection", "erp.material", "load.deletes", {"detect": "none", "apply": "none"},
     "must detect deletes by key_compare"),
    ("mass-delete guard on a change feed", "erp.delivery", "load.mass_delete_max_share", 0.05,
     "applies only to full copies"),
    ("mass-delete share of zero", "erp.material", "load.mass_delete_max_share", 0, "less than or equal to the minimum"),
    ("unknown severity action", "lims.inspection_result", "quality.actions.major",
     {"rows": "delete", "dataset": "block"}, "is not one of"),
    ("recon entry compares a hop with itself", "erp.delivery", "reconciliation.entries.0.right", "sources",
     "compares sources with itself"),
    ("recon entry on an unknown column", "erp.delivery", "reconciliation.entries.0.keys", ["shipment_id"],
     "'shipment_id', which is not"),
    ("recon measure without tolerance", "erp.delivery", "reconciliation.entries.0.tolerance", {"deliveries": 0},
     "no tolerance for delivered_qty_total"),
    ("recon sum without a column", "erp.delivery", "reconciliation.entries.0.measures",
     [{"name": "deliveries", "agg": "count"}, {"name": "delivered_qty_total", "agg": "sum"}], "with no column"),
]


@pytest.mark.parametrize("name,key,path,value,error", DATASET_CASES, ids=[c[0] for c in DATASET_CASES])
def test_dataset_v02(name, key, path, value, error):
    errs = dataset_errors(key, path, value)
    assert errs == [] if error is None else any(error in e for e in errs), errs


def test_unknown_contract_severity():
    f, m = DOM["dataset"]["erp.delivery"]
    c = yaml.safe_load((f.parent / m["contract"]).read_text())
    c["schema"][0]["quality"][0]["severity"] = "blocker"
    assert any("'blocker' is not critical, major or minor" in e for e in ls.lint_dataset_v02(m, c, PLATFORM, "m"))


def test_severity_aliases_keep_slice_1_valid():
    c = {"schema": [{"properties": [], "quality": [{"severity": "error"}]}]}
    m = yaml.safe_load((ROOT / "slices/01-orders/manifest/orders.yaml").read_text())
    assert ls.lint_dataset_v02(m, c, PLATFORM, "m") == []


def gold_errors(name, path, value):
    f, g = DOM["gold"][name]
    c = yaml.safe_load((f.parent / g["contract"]).read_text())
    g2 = g if path is None else put(g, path, value)
    errs = ls._schema_errors(V["gold"], g2, name)
    if errs:
        return errs
    inputs = set().union(*[DS_COLS.get(i["dataset"], set()) for i in g2["inputs"]])
    return ls.lint_gold(g2, c, DS_COLS, DIMS, name, inputs)


GOLD_CASES = [
    ("modelled fact valid", "fact_otif", None, None, None),
    ("dataframe build valid", "fact_scrap", None, None, None),
    ("dimension valid", "dim_dealer", None, None, None),
    ("engine name as build kind", "fact_scrap", "build.kind", "pyspark", "is not one of"),
    ("modelled fact without build", "fact_otif", "build", DEL, "'build' is a required property"),
    ("modelled fact without window", "fact_otif", "window", DEL, "'window' is a required property"),
    ("one-to-one table with a build", "dim_dealer", "build", {"kind": "sql", "ref": "x.sql"}, "has no build()"),
    ("one-to-one with two inputs", "dim_dealer", "inputs", [{"dataset": "dealer_api.dealer"}, {"dataset": "erp.delivery"}],
     "exactly one input"),
    ("materialized view over two inputs", "fact_otif", "materialize", "materialized_view", "(ADR-006)"),
    ("grain column not in contract", "fact_otif", "grain", ["order_id", "line"], "'line', which is not"),
    ("window column not in contract", "fact_otif", "window.column", "ship_date", "'ship_date', which is not"),
    ("input with no manifest", "fact_otif", "inputs.1.dataset", "erp.invoice", "erp.invoice has no dataset manifest"),
    ("dimension with no manifest", "fact_otif", "dimensions.0.name", "dim_customer", "dim_customer has no gold_dimension"),
    ("as-of column nowhere", "fact_otif", "dimensions.0.as_of", "booked_ts", "'booked_ts' is in neither"),
    ("reserved member changed", "fact_otif", "keys.unknown_member", 0, "-1 was expected"),
    ("sequence surrogate keys", "fact_otif", "keys.surrogate", "identity", "'hash' was expected"),
    ("wrong contract pin", "fact_otif", "contract_version", "0.2.0", "pins contract 0.2.0"),
    ("modelled fact without grain check", "fact_otif", "checks.grain_unique", False, "checks its grain is unique"),
    ("dimension without history", "dim_dealer", "history", DEL, "'history' is a required property"),
    ("bad table name", "fact_otif", "name", "otif", "does not match"),
]


@pytest.mark.parametrize("name,table,path,value,error", GOLD_CASES, ids=[c[0] for c in GOLD_CASES])
def test_gold(name, table, path, value, error):
    errs = gold_errors(table, path, value)
    assert errs == [] if error is None else any(error in e for e in errs), errs


def metric_errors(name, path, value):
    mv = DOM["metric"][name][1]
    mv2 = mv if path is None else put(mv, path, value)
    return ls._schema_errors(V["metric"], mv2, name) or ls.lint_metric(mv2, FACTS, DIMS, name)


METRIC_CASES = [
    ("valid as written", "mv_otif", None, None, None),
    ("certified without a known answer", "mv_otif", "measures.0.known_answer", DEL, "has no known-answer test"),
    ("certified without synonyms", "mv_otif", "measures.0.synonyms", [], "has no synonyms"),
    ("unknown source fact", "mv_otif", "source", "fact_returns", "has no gold_fact manifest"),
    ("unknown join", "mv_otif", "joins", ["dim_customer"], "has no gold_dimension manifest"),
    ("time dimension not a dimension", "mv_otif", "measures.0.time_dimension", "Week", "'Week', which is not a dimension"),
    ("unknown certification", "mv_otif", "measures.0.certification", "approved", "is not one of"),
    ("additivity unstated", "mv_otif", "measures.0.additive", DEL, "'additive' is a required property"),
    ("name without mv_", "mv_otif", "name", "otif", "does not match"),
]


@pytest.mark.parametrize("name,mv,path,value,error", METRIC_CASES, ids=[c[0] for c in METRIC_CASES])
def test_metric(name, mv, path, value, error):
    errs = metric_errors(mv, path, value)
    assert errs == [] if error is None else any(error in e for e in errs), errs


MODEL = DOM["model"]["dealer_demand_forecast"][1]
MODEL_CASES = [
    ("valid as written", None, None, None),
    ("feature from a table that is not gold", "features.0.source", "dealer_sellout", "is not a gold table"),
    ("feature column not in contract", "features.0.columns", ["margin"], "fact_sales.margin is not in its contract"),
    ("target column not in contract", "target.column", "units", "fact_sales.units is not in its contract"),
    ("training as-of not a target column", "training.as_of", "order_ts", "is not a column of the target's source"),
    ("no limitations", "limitations", [], "should be non-empty"),
    ("no metric threshold", "metric.threshold", DEL, "'threshold' is a required property"),
    ("unknown status", "status", "live", "is not one of"),
]


@pytest.mark.parametrize("name,path,value,error", MODEL_CASES, ids=[c[0] for c in MODEL_CASES])
def test_ml_model(name, path, value, error):
    md = MODEL if path is None else put(MODEL, path, value)
    errs = ls._schema_errors(V["ml_model"], md, "m") or ls.lint_model(md, GOLD_COLS, "m")
    assert errs == [] if error is None else any(error in e for e in errs), errs


PLATFORM_CASES = [
    ("valid as written", None, None, None),
    ("no default for critical", "quality_defaults.critical", DEL, "'critical' is a required property"),
    ("agent acting directly", "agents.2.autonomy", "act", "is not one of"),
    ("agent without tools", "agents.0.tools", [], "should be non-empty"),
    ("unknown environment", "environments", ["dev", "staging"], "is not one of"),
    ("time zone not a zone", "business_timezone", "IST", "does not match"),
]


@pytest.mark.parametrize("name,path,value,error", PLATFORM_CASES, ids=[c[0] for c in PLATFORM_CASES])
def test_platform(name, path, value, error):
    p = PLATFORM if path is None else put(PLATFORM, path, value)
    errs = ls._schema_errors(V["platform"], p, "p")
    assert errs == [] if error is None else any(error in e for e in errs), errs


def test_missing_platform_default_for_a_used_severity():
    f, m = DOM["dataset"]["erp.delivery"]
    c = yaml.safe_load((f.parent / m["contract"]).read_text())
    p = put(PLATFORM, "quality_defaults.critical", DEL)
    assert any("no action for severity 'critical'" in e for e in ls.lint_dataset_v02(m, c, p, "m"))
