"""DBS binding checks (DE-023): each row breaks the slice 1 Databricks binding in one way."""
import copy
import json
import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import lint  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
B = yaml.safe_load((ROOT / "slices/01-orders/binding-databricks.yaml").read_text())
SCHEMA = json.loads((ROOT / "dbs/schema/binding.schema.json").read_text())
PORTS = lint.load_ports()
DAC = {r["id"] for r in lint.load_obligations()}


def edit(fn):
    b = copy.deepcopy(B)
    fn(b)
    return b


CASES = [
    ("valid as written", lambda b: None, None),
    ("wrong apiVersion", lambda b: b.update(apiVersion="harness-profile/v1"), "was expected"),
    ("no accepted_gaps block", lambda b: b.pop("accepted_gaps"), "'accepted_gaps' is a required property"),
    ("unknown approach", lambda b: b["bindings"]["mover"].update(approach="magic"), "is not one of"),
    ("unknown coverage", lambda b: b["bindings"]["mover"].update(coverage="mostly"), "is not one of"),
    ("partial without a gap", lambda b: b["bindings"]["table_writer"].pop("gap"), "'gap' is a required property"),
    ("none without a filler", lambda b: b["bindings"]["reconciler"].pop("gap_filled_by"),
     "'gap_filled_by' is a required property"),
    ("gap filled by a product", lambda b: b["bindings"]["reconciler"]["gap_filled_by"].update(approach="platform"),
     "is not one of"),
    ("binds an unknown port", lambda b: b["bindings"].update(
        warp_drive={"approach": "platform", "adapter": "x", "coverage": "full", "proves": []}), "not a port"),
    ("proves an unknown obligation", lambda b: b["bindings"]["mover"].update(proves=["ZZZ-99"]),
     "not a DAC obligation"),
    ("gap with a short reason", lambda b: b["accepted_gaps"].append(
        {"obligation": "OPS-01", "reason": "later", "owner": "a", "review": "2026-12-01"}), "is too short"),
    ("decision without its source", lambda b: b["decisions"].update(D6={"value": "x"}),
     "'source' is a required property"),
]


@pytest.mark.parametrize("name,change,error", CASES, ids=[c[0] for c in CASES])
def test_binding(name, change, error):
    errs = lint.lint_binding(edit(change), SCHEMA, {p["port"] for p in PORTS}, DAC, "b")
    assert errs == [] if error is None else any(error in e for e in errs), errs


def test_every_slice_binding_is_clean():
    assert lint.lint_bindings() == []


def test_coverage_by_concern_lists_every_bound_port():
    cov = lint.coverage_by_concern(B, PORTS)
    bound = {p for rows in cov.values() for p, c, _ in rows if c != "unbound"}
    assert bound == set(B["bindings"]) & {p["port"] for p in PORTS}
