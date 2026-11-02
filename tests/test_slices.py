"""Slice 1 cross-checks: the five files must agree with each other and with DAC and DPC.
Run: uv run --with pytest --with pyyaml --with jsonschema pytest -q"""
import copy
import json
import sys
from pathlib import Path

import jsonschema
import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import lint  # noqa: E402

ROOT = lint.ROOT
SLICE = ROOT / "slices" / "01-orders"
y = lambda p: yaml.safe_load((SLICE / p).read_text())  # noqa: E731

CONTRACT = y("contracts/orders.odcs.yaml")
MANIFEST = y("manifest/orders.yaml")
WORLD = y("world.yaml")
BINDING = y("binding-databricks.yaml")
DAC = {r["id"] for r in lint.load_obligations()}
CAPS = {c["id"]: c for c in lint.load_capabilities()}
PORTS = {p["port"] for p in lint.load_ports()}
VOCAB = lint.load_vocab()
ODCS = json.loads((ROOT / "core" / "odcs-json-schema-v3.2.0.json").read_text())
PROPS = {p["name"] for o in CONTRACT["schema"] for p in o["properties"]}


def odcs_errors(doc):
    v = jsonschema.validators.validator_for(ODCS)(ODCS)
    return [e.message for e in v.iter_errors(doc)]


def broken(**changes):
    d = copy.deepcopy(CONTRACT)
    d.update(changes)
    return d


# The validator must accept our contract and reject broken ones, or a pass means nothing.
ODCS_CASES = [
    ("slice 1 contract", CONTRACT, True),
    ("unknown api version", broken(apiVersion="v9.9.9"), False),
    ("wrong kind", broken(kind="Contract"), False),
    ("missing id", {k: v for k, v in CONTRACT.items() if k != "id"}, False),
    ("unknown quality metric", broken(schema=[{**CONTRACT["schema"][0], "quality": [{"type": "library", "metric": "orphans"}]}]), False),
    ("DAMA word as dimension", broken(schema=[{**CONTRACT["schema"][0], "quality": [{"type": "library", "metric": "rowCount", "dimension": "validity"}]}]), False),
]


@pytest.mark.parametrize("name,doc,ok", ODCS_CASES, ids=[c[0] for c in ODCS_CASES])
def test_contract_against_odcs(name, doc, ok):
    assert (odcs_errors(doc) == []) is ok


# (name, condition) pairs: each must hold for the slice to be consistent.
CHECKS = [
    ("manifest points at the contract", (SLICE / "manifest" / MANIFEST["contract"]).resolve() == (SLICE / "contracts" / "orders.odcs.yaml").resolve()),
    ("manifest pins the contract version", MANIFEST["contract_version"] == CONTRACT["version"]),
    ("world cites the same contract", WORLD["cites"]["contract"]["id"] == CONTRACT["id"] and WORLD["cites"]["contract"]["version"] == CONTRACT["version"]),
    ("watermark column is in the contract", MANIFEST["config"]["watermark_column"] in PROPS),
    ("history order column is in the contract", MANIFEST["load"]["history_order_by"] in PROPS),
    ("dedup keys and order are in the contract", set(MANIFEST["dedup"]["business_keys"] + [MANIFEST["dedup"]["order_by"]]) <= PROPS),
    ("reconciled columns are in the contract", {m["column"] for m in MANIFEST["reconciliation"]["measures"] if "column" in m} <= PROPS),
    ("every measure has a tolerance", {m["name"] for m in MANIFEST["reconciliation"]["measures"]} <= set(MANIFEST["reconciliation"]["tolerance"])),
    ("reconciled hops are spine stages", set(MANIFEST["reconciliation"]["hops"]) <= set(VOCAB["stages"])),
    ("manifest archetypes exist", set(MANIFEST["archetypes"]) <= set(VOCAB["archetypes"])),
    ("the four planned incidents are on the calendar", {e["kind"] for e in WORLD["calendar"]} == {"duplicate_delivery", "source_delete", "late_change", "renamed_column"}),
    ("every incident's detector is a DAC obligation", all(e["expect"]["detector"] in DAC for e in WORLD["calendar"])),
    ("every incident is handled by a slice 1 capability", all(c in CAPS and CAPS[c].get("slice") == 1 for e in WORLD["calendar"] for c in e["expect"]["handled_by"])),
    ("every handling capability discharges the detector", all(e["expect"]["detector"] in CAPS[c]["discharges"] or any(e["expect"]["detector"] in CAPS[x]["discharges"] for x in e["expect"]["handled_by"]) for e in WORLD["calendar"] for c in e["expect"]["handled_by"])),
    ("the renamed column exists in the contract", "amount" in PROPS),
    ("every bound port exists", set(BINDING["ports"]) <= PORTS),
    ("every port slice 1 uses is bound", {c["port"] for c in CAPS.values() if c.get("slice") == 1 and c.get("port")} <= set(BINDING["ports"])),
    ("binding verify ids are DAC obligations", all(i in DAC for p in BINDING["ports"].values() for i in p["verify_with"])),
    ("not-covered ids are DAC obligations", all(n["obligation"] in DAC for n in BINDING["not_covered"])),
]


@pytest.mark.parametrize("name,holds", CHECKS, ids=[c[0] for c in CHECKS])
def test_slice1_consistent(name, holds):
    assert holds, name


def test_no_product_names_outside_the_binding():
    for f in ("world.yaml", "manifest/orders.yaml", "contracts/orders.odcs.yaml", "README.md"):
        text = (SLICE / f).read_text().replace("binding-databricks.yaml", "")  # the binding's own file name
        hits = lint.products_in(text)
        assert hits == [], f"{f}: {hits}"
