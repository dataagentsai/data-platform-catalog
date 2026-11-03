"""Two-layer DBS checks (decision M1, ADR-014): engine and cloud layers, composed by stacks.
Each row breaks one layer or one stack in one way and names the error expected."""
import copy
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import coverage  # noqa: E402
import lint  # noqa: E402
import lint_shape  # noqa: E402

ROOT = lint.ROOT
PORTS = lint.load_ports()
PORT_NAMES = {p["port"] for p in PORTS}
DAC = {r["id"] for r in lint.load_obligations()}
LAYERS = lint_shape.load_layers()
STACKS = lint_shape.load_stacks()
LV = lint_shape._validator(ROOT / "dbs" / "schema", "layer.schema.json")
SV = lint_shape._validator(ROOT / "dbs" / "schema", "stack.schema.json")
BSCHEMA = json.loads((ROOT / "dbs" / "schema" / "binding.schema.json").read_text())
ENGINE, CLOUD = ("engine", "databricks"), ("cloud", "aws")
OBJ = {"approach": "cloud-native", "adapter": "x", "coverage": "full", "proves": []}


def layer(key, fn):
    d = copy.deepcopy(LAYERS[key])
    fn(d)
    return d


LAYER_CASES = [
    ("engine valid as written", ENGINE, lambda d: None, None),
    ("cloud valid as written", CLOUD, lambda d: None, None),
    ("wrong apiVersion", ENGINE, lambda d: d.update(apiVersion="data-binding/v0.1"), "was expected"),
    ("layer word wrong", CLOUD, lambda d: d.update(layer="engine"), "lives in dbs/cloud/"),
    ("name does not match file", ENGINE, lambda d: d.update(name="fabric"), "does not match the file name"),
    ("engine binds a cloud-only port", ENGINE, lambda d: d["bindings"].update(object_store=OBJ),
     "port object_store may be bound by ['cloud'], not by the engine layer"),
    ("cloud binds an engine-only port", CLOUD, lambda d: d["bindings"].update(table_writer=OBJ),
     "port table_writer may be bound by ['engine'], not by the cloud layer"),
    ("unknown port", CLOUD, lambda d: d["bindings"].update(warp_drive=OBJ), "not a port in dpc/ports.yaml"),
    ("proves an unknown obligation", CLOUD, lambda d: d["bindings"]["key_manager"].update(proves=["ZZZ-99"]),
     "not a DAC obligation"),
    ("partial without a gap", CLOUD, lambda d: d["bindings"]["mover"].pop("gap"), "'gap' is a required property"),
    ("profile unbinds what the base never bound", ENGINE,
     lambda d: d["profiles"]["free-edition"]["unbind"].append("object_store"), "which the base does not bind"),
    ("profile binds a cloud-only port", ENGINE,
     lambda d: d["profiles"]["free-edition"]["bindings"].update(key_manager=OBJ), "not by the engine layer"),
    ("profile without a summary", ENGINE, lambda d: d["profiles"]["free-edition"].pop("summary"),
     "'summary' is a required property"),
]


@pytest.mark.parametrize("name,key,change,error", LAYER_CASES, ids=[c[0] for c in LAYER_CASES])
def test_layer(name, key, change, error):
    errs = lint_shape.lint_layer(key, layer(key, change), LV, PORTS, DAC)
    assert errs == [] if error is None else any(error in e for e in errs), errs


def stack(name, fn):
    s = copy.deepcopy(STACKS[name])
    fn(s)
    return s


STACK_CASES = [
    ("aws valid as written", "aws-databricks", lambda s: None, None),
    ("free edition valid as written", "free-edition", lambda s: None, None),
    ("double binding left unresolved", "aws-databricks", lambda s: s["prefer"].pop("secret_store"),
     "both layers bind secret_store"),
    ("prefer for a port only one layer binds", "aws-databricks", lambda s: s["prefer"].update(table_writer="engine"),
     "prefer names table_writer, which only one layer binds"),
    ("prefer an unknown layer word", "aws-databricks", lambda s: s["prefer"].update(secret_store="vendor"),
     "is not one of"),
    ("unknown engine profile", "free-edition", lambda s: s["engine"].update(profile="trial"), "has no profile 'trial'"),
    ("unknown cloud layer", "aws-databricks", lambda s: s["cloud"].update(layer="gcp"), "no cloud layer dbs/cloud/gcp.yaml"),
    ("unknown engine layer", "free-edition", lambda s: s["engine"].update(layer="fabric"),
     "no engine layer dbs/engine/fabric.yaml"),
    ("name does not match file", "free-edition", lambda s: s.update(name="trial"), "does not match the file name"),
    ("gap on an unknown obligation", "free-edition", lambda s: s["accepted_gaps"].append(
        {"obligation": "ZZZ-01", "reason": "a reason that is long enough", "owner": "a", "review": "2026-12-01"}),
     "not a DAC obligation"),
]


@pytest.mark.parametrize("name,stack_name,change,error", STACK_CASES, ids=[c[0] for c in STACK_CASES])
def test_stack(name, stack_name, change, error):
    errs = lint_shape.lint_stack(stack_name, stack(stack_name, change), SV, LAYERS, BSCHEMA, PORT_NAMES, DAC)
    assert errs == [] if error is None else any(error in e for e in errs), errs


@pytest.mark.parametrize("port,winner", sorted(STACKS["aws-databricks"]["prefer"].items()))
def test_prefer_picks_the_named_layer(port, winner):
    b = lint_shape.compose(STACKS["aws-databricks"], LAYERS)
    want = (LAYERS[ENGINE] if winner == "engine" else LAYERS[CLOUD])["bindings"][port]["adapter"]
    assert b["bindings"][port]["adapter"] == want
    assert b["bindings"][port]["settings"]["also_bound_by_other_layer"]


def test_free_edition_keeps_what_slice_1_proved():
    b = lint_shape.compose(STACKS["free-edition"], LAYERS)
    assert "Unity Catalog volume" in b["bindings"]["landing_store"]["adapter"]
    assert "identity_provider" not in b["bindings"]
    assert {"SCH-01", "OPS-01", "GATE-02"} <= {g["obligation"] for g in b["accepted_gaps"]}


def test_aws_stack_binds_every_port():
    assert set(lint_shape.compose(STACKS["aws-databricks"], LAYERS)["bindings"]) == PORT_NAMES


def test_every_port_says_which_layer_binds_it():
    assert all(set(p["binds_in"]) <= {"engine", "cloud"} and p["binds_in"] for p in PORTS)


def test_whole_dbs_is_clean():
    assert lint_shape.lint_dbs() == []


@pytest.mark.parametrize("name", sorted(STACKS))
def test_coverage_file_is_current(name):
    want = coverage.render(name, STACKS[name], LAYERS, PORTS)
    assert (ROOT / "dbs" / "stacks" / f"{name}.COVERAGE.md").read_text() == want
