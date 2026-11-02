"""DPM manifest checks (DE-022): each row breaks the slice 1 manifest in one way and names the error expected."""
import copy
import json
import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from lint import lint_manifest, lint_manifests  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
M = yaml.safe_load((ROOT / "slices/01-orders/manifest/orders.yaml").read_text())
C = yaml.safe_load((ROOT / "slices/01-orders/contracts/orders.odcs.yaml").read_text())
KEYS = yaml.safe_load((ROOT / "dpm/keys.yaml").read_text())
SCHEMA = json.loads((ROOT / "dpm/schema/dataset.schema.json").read_text())
ARCH = set(yaml.safe_load((ROOT / "core/archetypes.yaml").read_text()))


def broken(path, value):
    m = copy.deepcopy(M)
    *parents, last = path.split(".")
    node = m
    for p in parents:
        node = node[p]
    if value is DELETE:
        del node[last]
    else:
        node[last] = value
    return m


DELETE = object()

CASES = [
    ("valid as written", None, None, None),
    ("no contract", "contract", DELETE, "'contract' is a required property"),
    ("contract not ODCS", "contract", "orders.json", "does not match"),
    ("unpinned version", "contract_version", "latest", "does not match"),
    ("wrong pin", "contract_version", "0.2.0", "pins contract 0.2.0"),
    ("unknown config key", "config.freshness_warn_after_hours", "4", "not in dpm/keys.yaml"),
    ("config value not a string", "config.sla_freshness_hours", 4, "is not of type 'string'"),
    ("history without order", "load.history_order_by", DELETE, "'history_order_by' is a required property"),
    ("order by unknown column", "load.history_order_by", "arrived_at", "not a contract column"),
    ("unknown load pattern", "load.pattern", "magic", "is not one of"),
    ("unknown delete detection", "load.deletes.detect", "guess", "is not one of"),
    ("measure on unknown column", "reconciliation.measures", [{"name": "x", "column": "price"}], "not a contract column"),
    ("one hop only", "reconciliation.hops", ["silver"], "is too short"),
    ("unknown archetype", "archetypes", ["PA99"], "not in core/archetypes.yaml"),
    ("bad archetype id", "archetypes", ["A1"], "does not match"),
    ("volume band upside down", "volume.expected_rows_per_delivery", {"min": 10, "max": 1}, "is above max"),
    ("waiver without approver", "waivers", [{"concern": "X5", "reason": "profiling later", "expires": "2026-12-31"}],
     "'approver' is a required property"),
    ("waiver on unknown concern", "waivers", [{"concern": "X23", "reason": "no such concern", "approver": "a",
                                               "expires": "2026-12-31"}], "does not match"),
    ("extra top-level field", "pipeline_sql", "SELECT 1", "Additional properties are not allowed"),
]


@pytest.mark.parametrize("name,path,value,error", CASES, ids=[c[0] for c in CASES])
def test_manifest(name, path, value, error):
    m = M if path is None else broken(path, value)
    errs = lint_manifest(m, C, KEYS, SCHEMA, ARCH, "m")
    if error is None:
        assert errs == []
    else:
        assert any(error in e for e in errs), errs


def test_every_slice_manifest_is_clean():
    assert lint_manifests() == []


def test_proposed_keys_are_not_already_registered():
    assert not {p["key"] for p in KEYS["proposed"]} & set(KEYS["dataset_config"])
