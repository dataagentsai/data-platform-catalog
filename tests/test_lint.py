"""Table-driven tests for scripts/lint.py.  Run: uv run --with pytest --with pyyaml pytest -q"""
import copy
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import lint  # noqa: E402

VOCAB = lint.load_vocab()

GOOD = {
    "_file": "X15", "id": "DUP-01", "status": "draft", "since": "0.1.0", "title": "Same batch twice",
    "concern": "X15", "level": "MUST", "core": True, "dimension": "uniqueness", "stages": ["bronze"],
    "statement": "A batch delivered twice MUST NOT change any total.", "failure_mode": "Revenue doubled.",
    "test": "Load the same file twice.", "evidence": "A file fingerprint.",
    "cites": [{"standard": "ODCS", "ref": "quality[].metric = duplicateValues"}], "related": [],
}


def with_(**changes):
    r = copy.deepcopy(GOOD)
    for k, v in changes.items():
        if v is DROP:
            r.pop(k)
        else:
            r[k] = v
    return r


DROP = object()

CASES = [
    # (name, record, expected error fragment or None for clean)
    ("valid record", with_(), None),
    ("null dimension is allowed", with_(dimension=None), None),
    ("empty cites is allowed", with_(cites=[]), None),
    ("missing statement", with_(statement=DROP), "missing 'statement'"),
    ("missing stages", with_(stages=[]), "missing 'stages'"),
    ("cites not a list", with_(cites=DROP), "'cites' must be a list"),
    ("bad id shape", with_(id="dup-1"), "id must look like ABC-01"),
    ("unknown status", with_(status="final"), "unknown status"),
    ("unknown concern", with_(concern="X99"), "unknown concern 'X99'"),
    ("concern in wrong file", with_(concern="X4"), "concern X4 is in file X15.yaml"),
    ("unknown level", with_(level="SHALL"), "level must be MUST, SHOULD or MAY"),
    ("statement lacks level word", with_(statement="A batch twice changes nothing."), "does not use its level word"),
    ("core not boolean", with_(core="yes"), "core must be true or false"),
    ("DAMA word is not an ODCS dimension", with_(dimension="validity"), "not an ODCS 3.2.0 dimension"),
    ("unknown stage", with_(stages=["platinum"]), "unknown stage 'platinum'"),
    ("cite to unknown standard", with_(cites=[{"standard": "ISO-8000", "ref": "x"}]), "unknown standard"),
    ("cite without ref", with_(cites=[{"standard": "ODCS"}]), "has no ref"),
    ("related id missing", with_(related=["NOPE-01"]), "related id 'NOPE-01' does not exist"),
    ("relates to itself", with_(related=["DUP-01"]), "relates to itself"),
    ("product name in statement", with_(statement="A batch MUST NOT double in Snowflake."), "product name 'snowflake'"),
    ("product name in test", with_(test="Use Auto Loader twice."), "product name 'auto loader'"),
    ("product word inside another word is fine", with_(test="Load glueless data twice."), None),
]


@pytest.mark.parametrize("name,rec,want", CASES, ids=[c[0] for c in CASES])
def test_lint_record(name, rec, want):
    errs = lint.lint([rec], VOCAB)
    if want is None:
        assert errs == []
    else:
        assert any(want in e for e in errs), errs


def test_duplicate_id():
    errs = lint.lint([with_(), with_()], VOCAB)
    assert any("duplicate id" in e for e in errs)


def test_real_catalog_is_clean():
    recs = lint.load_obligations()
    assert len(recs) >= 30
    assert lint.lint(recs, VOCAB) + lint.lint_triage(recs) == []


def test_index_is_up_to_date():
    import index
    assert (lint.ROOT / "dac" / "INDEX.md").read_text() == index.render(), "run: uv run scripts/index.py"


def test_every_concern_has_an_obligation():
    have = {r["concern"] for r in lint.load_obligations()}
    assert set(VOCAB["concerns"]) - have == set()


# ---------- ports ----------
DAC_IDS = {r["id"] for r in lint.load_obligations()}

GOOD_PORT = {
    "port": "table_writer", "status": "draft", "since": "0.1.0", "service": "A", "tier": "core",
    "concerns": ["X15"], "stages": ["silver"], "summary": "Writes rows.", "kernel_owns": "The batch key.",
    "supplied_outside": "The table format.", "operations": [{"name": "write", "intent": "Write a batch."}],
    "invariants": [{"must": "Twice changes nothing.", "because": "Resends.", "obligation": "DUP-01",
                    "checkable": "dynamic"}],
}


def port_(**changes):
    p = copy.deepcopy(GOOD_PORT)
    p.update(changes)
    return p


PORT_CASES = [
    ("valid port", port_(), None),
    ("missing summary", port_(summary=""), "missing 'summary'"),
    ("name not snake case", port_(port="TableWriter"), "lower_snake_case"),
    ("unknown service", port_(service="D"), "service must be A, B, C or platform"),
    ("unknown tier", port_(tier="soon"), "tier must be core or later"),
    ("unknown concern", port_(concerns=["X0"]), "unknown concern 'X0'"),
    ("unknown stage", port_(stages=["lake"]), "unknown stage 'lake'"),
    ("operation without intent", port_(operations=[{"name": "write"}]), "needs a name and an intent"),
    ("invariant to unknown obligation", port_(invariants=[{**GOOD_PORT["invariants"][0], "obligation": "XX-01"}]),
     "is not a DAC id"),
    ("invariant bad checkable", port_(invariants=[{**GOOD_PORT["invariants"][0], "checkable": "manual"}]),
     "static or dynamic"),
    ("product in kernel_owns", port_(kernel_owns="The Kafka offset."), "product name 'kafka'"),
]


@pytest.mark.parametrize("name,port,want", PORT_CASES, ids=[c[0] for c in PORT_CASES])
def test_lint_port(name, port, want):
    errs = lint.lint_ports([port], VOCAB, DAC_IDS)
    assert errs == [] if want is None else any(want in e for e in errs), errs


def test_duplicate_port():
    assert any("duplicate port" in e for e in lint.lint_ports([port_(), port_()], VOCAB, DAC_IDS))


# ---------- capabilities ----------
GOOD_CAP = {
    "_file": "X15", "id": "DPC-0001", "status": "draft", "since": "0.1.0", "level": "MUST",
    "title": "Every write carries a batch key", "concern": "X15", "stages": ["bronze"], "archetypes": ["PA1"],
    "core": True, "port": "table_writer", "requirement": "Every write MUST carry its batch key.",
    "failure_mode": "Revenue doubled.", "discharges": ["DUP-01"], "realization_policy": "own",
    "design_decisions": [{"key": "k", "question": "q?", "tension": "t", "resolution": "r"}], "see_also": [],
}
PORTS = {"table_writer"}


def cap_(**changes):
    c = copy.deepcopy(GOOD_CAP)
    c.update(changes)
    return c


CAP_CASES = [
    ("valid capability", cap_(), None),
    ("kernel-only capability has no port", cap_(port=None), None),
    ("bad id", cap_(id="DPC-1"), "id must look like DPC-0001"),
    ("missing requirement", cap_(requirement=""), "missing 'requirement'"),
    ("requirement lacks level word", cap_(requirement="Every write carries a key."), "level word"),
    ("unknown archetype", cap_(archetypes=["A6"]), "unknown archetype 'A6'"),
    ("unknown port", cap_(port="writer"), "unknown port 'writer'"),
    ("discharges unknown obligation", cap_(discharges=["NOPE-01"]), "not a DAC id"),
    ("bad realization policy", cap_(realization_policy="buy"), "own, adopt or bind"),
    ("half a design decision", cap_(design_decisions=[{"key": "k", "question": "q?"}]), "missing 'tension'"),
    ("see_also missing", cap_(see_also=["DPC-0099"]), "see_also id 'DPC-0099'"),
    ("product in design decision", cap_(design_decisions=[{**GOOD_CAP["design_decisions"][0], "resolution": "Use dbt."}]),
     "product name 'dbt'"),
]


@pytest.mark.parametrize("name,cap,want", CAP_CASES, ids=[c[0] for c in CAP_CASES])
def test_lint_capability(name, cap, want):
    errs = lint.lint_capabilities([cap], VOCAB, DAC_IDS, PORTS)
    assert errs == [] if want is None else any(want in e for e in errs), errs


def test_uncovered_lists_obligations_no_capability_discharges():
    obligations = [{"id": "DUP-01"}, {"id": "DUP-02"}]
    assert lint.uncovered(obligations, [cap_()]) == ["DUP-02"]


def test_real_ports_archetypes_and_capabilities_are_clean():
    ports = lint.load_ports()
    assert lint.lint_archetypes(VOCAB) == []
    assert lint.lint_ports(ports, VOCAB, DAC_IDS) == []
    assert lint.lint_capabilities(lint.load_capabilities(), VOCAB, DAC_IDS, {p["port"] for p in ports}) == []


# The five DAC obligations session B proposed (Goal 1b): each sits in its concern file, is discharged by the
# capabilities named in the proposal, and is cited by the ADR named there.
SHAPE_CASES = [
    # (id, concern, level, capabilities that discharge it, ADRs that cite it)
    ("DEL-04", "X6", "MUST", ["DPC-0054"], ["ADR-016"]),
    ("HIST-05", "X15", "MUST", ["DPC-0082"], ["ADR-017"]),
    ("ML-01", "X13", "MUST", ["DPC-0050", "DPC-0061", "DPC-0077"], ["ADR-021"]),
    ("SERV-06", "X13", "MUST", ["DPC-0073", "DPC-0076"], ["ADR-022"]),
    ("OPS-06", "X8", "SHOULD", ["DPC-0056"], []),
]


@pytest.mark.parametrize("oid,concern,level,caps,adrs", SHAPE_CASES, ids=[c[0] for c in SHAPE_CASES])
def test_shape_obligation_is_linked(oid, concern, level, caps, adrs):
    import lint_shape
    rec = next(r for r in lint.load_obligations() if r["id"] == oid)
    assert (rec["concern"], rec["_file"], rec["level"], rec.get("origin")) == (concern, concern, level, "shape")
    by_id = {c["id"]: c for c in lint.load_capabilities()}
    assert all(oid in by_id[c]["discharges"] for c in caps)
    cited = {a["id"] for a in lint_shape.load_adrs() if oid in (a.get("dac") or [])}
    assert set(adrs) <= cited
