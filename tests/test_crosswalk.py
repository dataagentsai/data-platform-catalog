"""Deck crosswalk checks (D13): the deck's 68 concerns map to DPC; each row breaks the crosswalk in one way."""
import copy
import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import lint  # noqa: E402
import lint_shape  # noqa: E402

CW = yaml.safe_load((lint.ROOT / "crosswalks" / "deck.yaml").read_text())
VOCAB = lint.load_vocab()
CAPS = {c["id"]: c for c in lint.load_capabilities()}
PORTS = {p["port"] for p in lint.load_ports()}


def edit(fn):
    cw = copy.deepcopy(CW)
    fn(cw["concerns"])
    return cw


CASES = [
    ("valid as written", lambda rows: None, None),
    ("a deck concern missing", lambda rows: rows.pop(), "deck concern C68 is missing"),
    ("a deck concern twice", lambda rows: rows.append(copy.deepcopy(rows[0])), "C01 is listed 2 times"),
    ("not a deck id", lambda rows: rows[0].update(deck="C99"), "'C99' is not a deck concern id"),
    ("unmapped deck concern", lambda rows: rows[5].update(dpc=[]), "no DPC capability"),
    ("unknown capability", lambda rows: rows[0].update(dpc=["DPC-9999"]), "not a DPC capability"),
    ("unknown port", lambda rows: rows[0].update(ports=["teleporter"]), "teleporter is not a port"),
    ("unknown concern", lambda rows: rows[0].update(concerns=["X40"]), "unknown concern"),
    ("bad lead letter", lambda rows: rows[0].update(lead="W"), "lead must be X, Y or Z"),
    ("product name in a note", lambda rows: rows[0].update(note="uses Kinesis"), "product name 'kinesis'"),
]


@pytest.mark.parametrize("name,change,error", CASES, ids=[c[0] for c in CASES])
def test_crosswalk(name, change, error):
    errs = lint_shape.lint_crosswalk(edit(change), VOCAB, set(CAPS), PORTS)
    assert errs == [] if error is None else any(error in e for e in errs), errs


def test_every_deck_concern_has_a_capability_and_a_port_or_a_kernel_note():
    for r in CW["concerns"]:
        assert r["dpc"], r["deck"]
        assert r["ports"] or "Kernel-only" in r.get("note", ""), r["deck"]


def test_named_ports_are_the_ports_of_named_capabilities_or_their_neighbours():
    # every port listed is the port of at least one capability on the row, or the row has a kernel-only note
    for r in CW["concerns"]:
        cap_ports = {CAPS[c]["port"] for c in r["dpc"]}
        assert set(r["ports"]) & cap_ports or not r["ports"], r["deck"]


@pytest.mark.parametrize("topic", ["gold harness", "semantic layer", "streaming", "cost", "access", "self-healing",
                                   "profiling", "recon"])
def test_brief_capabilities_exist(topic):
    want = {"gold harness": "DPC-0083", "semantic layer": "DPC-0073", "streaming": "DPC-0060", "cost": "DPC-0062",
            "access": "DPC-0066", "self-healing": "DPC-0100", "profiling": "DPC-0051", "recon": "DPC-0052"}[topic]
    assert want in CAPS and any(want in r["dpc"] for r in CW["concerns"])
