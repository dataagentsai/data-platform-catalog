"""Table-driven tests for layers/ (hard challenges and anti-patterns per layer and hop).
Run: uv run --with pytest --with pyyaml --with jsonschema pytest -q"""
import copy
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import lint  # noqa: E402
import lint_layers as ll  # noqa: E402
import lint_practices as lp  # noqa: E402

DAC = {o["id"] for o in lint.load_obligations()}
ADRS = lp.adr_ids()
PRACTICES = {p["id"]: p for p in lp.load_practices()}
REAL = ll.load_layers()


def good():
    return copy.deepcopy(REAL)


def test_real_layers_are_clean():
    assert ll.lint_layers(REAL, DAC, ADRS, PRACTICES) == []


def test_all_ten_layers_in_order():
    assert [x["id"] for x in REAL] == ll.ORDER


def _mut(fn):
    layers = good()
    fn(layers)
    return layers


CASES = [
    ("layer missing", lambda L: L.pop(3), "in that order"),
    ("layers out of order", lambda L: L.insert(0, L.pop(1)), "in that order"),
    ("wrong order number", lambda L: L[0].update(order=5), "order 5 should be 1"),
    ("unknown component", lambda L: L[0]["components"].append("teleporter"), "unknown component"),
    ("bad verdict", lambda L: L[0]["challenges"][0].update(verdict="maybe"), "verdict must be"),
    ("bad status", lambda L: L[0]["challenges"][0].update(status="soon"), "status must be"),
    ("unknown DAC", lambda L: L[0]["challenges"][0].update(dac=["NOPE-99"]), "unknown DAC id"),
    ("unknown ADR", lambda L: L[0]["challenges"][1].update(adr=["ADR-999"]), "unknown ADR"),
    ("unknown practice", lambda L: L[2]["challenges"][0].update(practices=["BP-999"]), "unknown practice"),
    ("no links", lambda L: L[0]["challenges"][0].update(dac=[], adr=[], practices=[]), "link at least one"),
    ("duplicate challenge id", lambda L: L[1]["challenges"].append(copy.deepcopy(L[0]["challenges"][0])), "duplicate id"),
    ("bad world day", lambda L: L[0]["challenges"][0].update(world_day=40), "world_day"),
    ("missing solution", lambda L: L[0]["challenges"][0].pop("solution"), "missing solution"),
    ("product name in solution", lambda L: L[0]["challenges"][0].update(solution="Load it with Kafka."), "rule R1"),
    ("practice that is not an anti-pattern", lambda L: L[1]["anti_patterns"].append({"practice": next(k for k, v in PRACTICES.items() if v["kind"] != "anti-pattern")}), "is not an anti-pattern"),
    ("unknown anti-pattern practice", lambda L: L[1]["anti_patterns"].append({"practice": "BP-999"}), "unknown practice BP-999"),
    ("new anti-pattern without new flag", lambda L: L[0]["anti_patterns"][0].pop("new"), "new: true"),
    ("new anti-pattern without instead", lambda L: L[0]["anti_patterns"][0].pop("instead"), "missing instead"),
]


@pytest.mark.parametrize("name,mutate,expect", CASES, ids=[c[0] for c in CASES])
def test_linter_refuses(name, mutate, expect):
    errs = ll.lint_layers(_mut(mutate), DAC, ADRS, PRACTICES)
    assert any(expect in e for e in errs), errs
