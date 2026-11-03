"""Slice 2, the tyre company (D17): contracts, manifests and the world must agree with each other and with DAC and
DPC, and the world must cover every demo story."""
import copy
import json
import sys
from pathlib import Path

import jsonschema
import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import lint  # noqa: E402
import lint_shape as ls  # noqa: E402

ROOT = lint.ROOT
D = ROOT / "slices" / "02-tyre"
DOM = ls.load_domain(D)
WORLD = yaml.safe_load((D / "world.yaml").read_text())
DAC = {r["id"] for r in lint.load_obligations()}
CAPS = {c["id"]: c for c in lint.load_capabilities()}
ODCS = json.loads((ROOT / "core" / "odcs-json-schema-v3.2.0.json").read_text())
CONTRACTS = sorted((D / "contracts").glob("*.odcs.yaml"))


@pytest.mark.parametrize("path", CONTRACTS, ids=[p.name for p in CONTRACTS])
def test_contract_is_valid_odcs(path):
    v = jsonschema.validators.validator_for(ODCS)(ODCS)
    assert [e.message for e in v.iter_errors(yaml.safe_load(path.read_text()))] == []


def test_every_contract_is_used_by_exactly_one_manifest():
    used = [(f.parent / m["contract"]).resolve() for kind in ("dataset", "gold") for f, m in DOM[kind].values()]
    assert sorted(used) == sorted(p.resolve() for p in CONTRACTS)


def test_whole_domain_is_clean():
    assert ls.lint_domain(D, CAPS, DAC, ls.STORIES) == []


def test_base_dataset_rules_hold():
    assert [e for f, _ in DOM["dataset"].values() for e in lint.lint_manifests_one(f)] == []


SOURCES = {"erp": "database", "mes": "database", "lims": "file_drop", "partner": "file_drop",
           "dealer_api": "rest_api", "press_stream": "stream"}


@pytest.mark.parametrize("source,kind", sorted(SOURCES.items()))
def test_brief_sources_are_in_the_world(source, kind):
    systems = [s for s in WORLD["systems"].values() if any(d.startswith(source + ".") for d in s["datasets"])]
    assert systems and systems[0]["kind"] == kind


@pytest.mark.parametrize("story", sorted(ls.STORIES))
def test_every_demo_story_has_an_incident(story):
    assert any(e["story"] == story for e in WORLD["calendar"])


@pytest.mark.parametrize("fact", ["fact_otif", "fact_scrap", "fact_sales"])
def test_brief_facts_are_modelled_with_a_build(fact):
    g = DOM["gold"][fact][1]
    assert g["pipeline"] == "modelled" and g["build"]["kind"] in ("sql", "dataframe")


@pytest.mark.parametrize("metric", ["mv_otif", "mv_scrap", "mv_sales"])
def test_each_metric_view_has_a_certified_measure(metric):
    assert any(m["certification"] == "certified" for m in DOM["metric"][metric][1]["measures"])


def test_every_ingest_mode_is_exercised():
    assert {m["ingest"]["mode"] for _, m in DOM["dataset"].values()} == {"push", "pull", "stream"}


def test_every_history_kind_is_exercised():
    assert {m["history"]["kind"] for _, m in DOM["dataset"].values()} == {"master", "transaction", "event", "snapshot"}


WORLD_CASES = [
    ("valid as written", lambda w: None, None),
    ("detector not in DAC", lambda w: w["calendar"][0]["expect"].update(detector="ZZZ-01"), "not a DAC obligation"),
    ("handler not in DPC", lambda w: w["calendar"][0]["expect"].update(handled_by=["DPC-9999"]), "not a DPC capability"),
    ("handlers do not discharge the detector", lambda w: w["calendar"][1]["expect"].update(handled_by=["DPC-0001"]),
     "no handling capability discharges"),
    ("incident after the clock ends", lambda w: w["calendar"][0].update(day=30), "outside the clock"),
    ("dataset no system delivers", lambda w: w["calendar"][0].update(dataset="erp.invoice"), "not delivered by any system"),
    ("unknown story", lambda w: w["calendar"][0].update(story="alien_invasion"), "unknown story"),
    ("no oracle", lambda w: w["calendar"][0]["expect"].pop("oracle"), "no oracle"),
    ("story dropped", lambda w: w.update(calendar=[e for e in w["calendar"] if e["story"] != "mass_delete"]),
     "required story mass_delete is not covered"),
    ("covers a story it never plants", lambda w: w.update(calendar=[e for e in w["calendar"] if e["story"] != "correction"]),
     "covers correction but no incident"),
    ("system dataset without manifest", lambda w: w["systems"]["erp_db"]["datasets"].append("erp.invoice"),
     "erp.invoice has no manifest"),
    ("product name in the world", lambda w: w["systems"]["erp_db"].update(note="SAP on Redshift"), "product name 'redshift'"),
    ("duplicate incident id", lambda w: w["calendar"].append(copy.deepcopy(w["calendar"][0])), "duplicate incident id"),
]


@pytest.mark.parametrize("name,change,error", WORLD_CASES, ids=[c[0] for c in WORLD_CASES])
def test_world(name, change, error):
    w = copy.deepcopy(WORLD)
    change(w)
    errs = ls.lint_world(w, set(DOM["dataset"]), CAPS, DAC, "w", ls.STORIES)
    assert errs == [] if error is None else any(error in e for e in errs), errs


def test_no_product_names_in_the_slice():
    for f in sorted(D.rglob("*")):
        if f.is_file():
            assert lint.products_in(f.read_text()) == [], f.name
