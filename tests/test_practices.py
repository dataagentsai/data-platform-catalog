"""Table-driven tests for practices/, enforced_by on DAC, and the generated page (goal G1, decision D12).
Run: uv run --with pytest --with pyyaml --with jsonschema pytest -q"""
import copy
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import build_practices_page as page  # noqa: E402
import lint  # noqa: E402
import lint_practices as lp  # noqa: E402

VOCAB = lint.load_vocab()
COMPS = lp.load_part("components")
DAC_IDS = {r["id"] for r in lint.load_obligations()}
BUNDLE = lp.load_bundle()
needs_bundle = pytest.mark.skipif(BUNDLE is None, reason="shift-left bundle not on this machine")
DROP = object()

GOOD = {
    "_file": "s2g", "id": "BP-090", "status": "draft", "since": "0.1.0", "kind": "anti-pattern",
    "title": "Appending to gold facts", "why": "Every retry double-counts.",
    "how": {"binding": "aws-databricks", "text": "The harness writes with replaceWhere on Delta only."},
    "instead": "Replace the whole window.", "layers": ["gold"], "components": ["s2g"],
    "enforced_by": [{"proposed": "SL-GOLD-01"}, {"runtime": "Unity Catalog grants refuse appends."}],
    "dac": ["GOLD-01"], "adr": ["ADR-006"],
}
PROPOSED = {"SL-GOLD-01"}


def with_(**changes):
    r = copy.deepcopy(GOOD)
    for k, v in changes.items():
        if v is DROP:
            r.pop(k)
        else:
            r[k] = v
    return r


CASES = [
    # (name, record, expected error fragment, or None for clean)
    ("valid anti-pattern", with_(), None),
    ("product names are fine in how and in enforcement notes", with_(), None),
    ("valid practice without instead", with_(kind="practice", instead=DROP), None),
    ("no adr is fine", with_(adr=DROP), None),
    ("principle lives in canon", with_(_file="canon", kind="principle", instead=DROP), None),
    ("missing dac", with_(dac=[]), "missing 'dac'"),
    ("unknown dac id", with_(dac=["NOPE-01"]), "dac 'NOPE-01' is not a DAC obligation"),
    ("missing why", with_(why=DROP), "missing 'why'"),
    ("bad id", with_(id="BP-90"), "id must look like BP-001"),
    ("unknown kind", with_(kind="rule"), "kind must be principle, practice or anti-pattern"),
    ("anti-pattern without instead", with_(instead=DROP), "an anti-pattern needs 'instead'"),
    ("practice with instead", with_(kind="practice"), "only an anti-pattern has 'instead'"),
    ("principle outside canon", with_(kind="principle", instead=DROP), "belongs in practices/canon.yaml"),
    ("practice in the wrong file", with_(_file="dq"), "belongs in practices/s2g.yaml"),
    ("unknown layer", with_(layers=["platinum"]), "unknown layer 'platinum'"),
    ("unknown component", with_(components=["s2g", "etl"]), "unknown component 'etl'"),
    ("how without binding", with_(how={"text": "x"}), "'how' must name its binding"),
    ("how as plain text", with_(how="Write with replaceWhere."), "'how' needs a text"),
    ("unknown adr", with_(adr=["ADR-999"]), "adr 'ADR-999' does not exist"),
    ("unknown enforcement kind", with_(enforced_by=[{"manual": "x"}]), "must be one of"),
    ("two keys in one enforcement entry", with_(enforced_by=[{"runtime": "x", "review": "y"}]), "must be one of"),
    ("empty enforcement note", with_(enforced_by=[{"review": ""}]), "enforced_by review is empty"),
    ("proposed check not listed", with_(enforced_by=[{"proposed": "SL-GOLD-99"}]), "not in practices/proposed"),
    ("product in title", with_(title="Appending to Delta facts"), "product name 'delta' in title"),
    ("product in why", with_(why="Genie gets it wrong."), "product name 'genie' in why"),
    ("product in instead", with_(instead="Use liquid clustering."), "product name 'liquid clustering' in instead"),
]


@pytest.mark.parametrize("name,rec,want", CASES, ids=[c[0] for c in CASES])
def test_lint_practice(name, rec, want):
    errs = lp.lint_practices([rec], VOCAB, COMPS, DAC_IDS, PROPOSED, lp.ADR_PLACEHOLDERS)
    assert errs == [] if want is None else any(want in e for e in errs), errs


def test_shift_left_id_must_be_in_the_bundle():
    rec = with_(enforced_by=[{"shift_left": ["SL-NOPE-01"]}])
    errs = lp.lint_practices([rec], VOCAB, COMPS, DAC_IDS, PROPOSED, lp.ADR_PLACEHOLDERS, bundle_ids={"SL-PURE-01"})
    assert any("'SL-NOPE-01' is not in the bundle" in e for e in errs), errs


def test_duplicate_id_and_reuse_of_a_dropped_id():
    assert any("duplicate id" in e for e in lp.lint_practices([with_(), with_()], VOCAB, COMPS, DAC_IDS, PROPOSED,
                                                               lp.ADR_PLACEHOLDERS))
    errs = lp.lint_practices([with_()], VOCAB, COMPS, DAC_IDS, PROPOSED, lp.ADR_PLACEHOLDERS, dropped_ids=["BP-090"])
    assert any("duplicate id" in e for e in errs), errs


# ---------- proposed checks ----------
GOOD_PROP = {"id": "SL-GOLD-01", "title": "Append write to a gold table", "stage": "commit",
             "catches": "An append write to a gold table.", "dac": ["GOLD-01"]}

PROP_CASES = [
    ("valid proposed check", {}, {"SL-GOLD-01"}, None, None),
    ("bad id", {"id": "GOLD-01"}, {"GOLD-01"}, None, "id must look like SL-AREA-01"),
    ("unknown stage", {"stage": "deploy"}, {"SL-GOLD-01"}, None, "stage must be one of"),
    ("unknown dac", {"dac": ["NOPE-01"]}, {"SL-GOLD-01"}, None, "dac 'NOPE-01' is not a DAC obligation"),
    ("no dac", {"dac": []}, {"SL-GOLD-01"}, None, "missing 'dac'"),
    ("no practice uses it", {}, set(), None, "no practice uses it (orphan)"),
    ("bundle has it now", {}, {"SL-GOLD-01"}, {"SL-GOLD-01"}, "the bundle has this check now"),
]


@pytest.mark.parametrize("name,change,used,bundle_ids,want", PROP_CASES, ids=[c[0] for c in PROP_CASES])
def test_lint_proposed(name, change, used, bundle_ids, want):
    errs = lp.lint_proposed([{**GOOD_PROP, **change}], DAC_IDS, used, bundle_ids)
    assert errs == [] if want is None else any(want in e for e in errs), errs


# ---------- enforced_by on DAC ----------
OBL = {"_file": "X15", "id": "GOLD-01", "test": "Run twice."}
FAKE_BUNDLE = {"SL-A-01": {"id": "SL-A-01", "dac": ["GOLD-01"]}, "SL-A-02": {"id": "SL-A-02", "dac": ["DUP-01"]}}
FAKE_PROPOSED = [{"id": "SL-GOLD-01", "dac": ["GOLD-01"]}]
GOOD_ENF = {"shift_left": ["SL-A-01"], "proposed": ["SL-GOLD-01"], "runtime": True, "review": None, "gap": None}

ENF_CASES = [
    ("valid", {}, {}, None),
    ("missing enforced_by", None, {}, "missing 'enforced_by'"),
    ("lacks a field", {"gap": DROP}, {}, "enforced_by lacks ['gap']"),
    ("shift_left out of date", {"shift_left": []}, {}, "shift_left is out of date"),
    ("proposed out of date", {"proposed": []}, {}, "proposed is out of date"),
    ("runtime not boolean", {"runtime": "yes"}, {}, "runtime must be true or false"),
    ("runtime without a test", {}, {"test": None}, "runtime is true but the obligation has no test"),
]


@pytest.mark.parametrize("name,change,rec_change,want", ENF_CASES, ids=[c[0] for c in ENF_CASES])
def test_lint_enforced_by(name, change, rec_change, want):
    rec = {**OBL, **rec_change}
    if change is not None:
        rec["enforced_by"] = {k: v for k, v in {**GOOD_ENF, **change}.items() if v is not DROP}
    errs = lp.lint_enforced_by([rec], FAKE_BUNDLE, FAKE_PROPOSED)
    assert errs == [] if want is None else any(want in e for e in errs), errs


GAP_CASES = [
    # (shift_left, proposed, runtime, review, gap, expected error or None)
    ([], [], True, None, lp.GAP_DEFAULT, None),
    ([], [], True, None, None, "no build-time check, so 'gap' must say so"),
    ([], [], False, None, "x", "nothing enforces it"),
    ([], [], False, "A person checks it.", "x", None),
]


@pytest.mark.parametrize("sl,prop,rt,rv,gap,want", GAP_CASES)
def test_gaps_are_marked(sl, prop, rt, rv, gap, want):
    rec = {"_file": "X1", "id": "CFG-04", "test": "t",
           "enforced_by": {"shift_left": sl, "proposed": prop, "runtime": rt, "review": rv, "gap": gap}}
    errs = lp.lint_enforced_by([rec], {}, [])
    assert errs == [] if want is None else any(want in e for e in errs), errs


def test_expected_enforced_is_the_reverse_of_the_check_links():
    want = lp.expected_enforced([{"id": "GOLD-01"}, {"id": "DUP-01"}], FAKE_BUNDLE, FAKE_PROPOSED)
    assert want == {"GOLD-01": {"shift_left": ["SL-A-01"], "proposed": ["SL-GOLD-01"]},
                    "DUP-01": {"shift_left": ["SL-A-02"], "proposed": []}}


# ---------- the real catalog ----------
def test_real_catalog_is_clean():
    errs, _, practices, _, dropped = lp.run(bundle=BUNDLE)
    assert errs == []
    assert len(practices) + len(dropped) == 134  # every card on the old page is kept or dropped with a reason


def test_every_practice_links_dac_and_every_new_obligation_is_used():
    practices = lp.load_practices()
    assert all(r["dac"] for r in practices)
    served = {d for r in practices for d in r["dac"]}
    new = {o["id"] for o in lint.load_obligations() if o.get("origin") == "deck"}
    assert new - served == set(), "a deck obligation no practice serves"


@needs_bundle
def test_page_is_deterministic_and_shows_every_practice_and_its_dac_ids():
    html = page.render(bundle=BUNDLE)
    assert html == page.render(bundle=BUNDLE)
    assert "/*@DATA@*/" not in html
    for r in lp.load_practices():
        assert f'"id":"{r["id"]}"' in html
        assert all(f'"{d}":[' in html for d in r["dac"])


@needs_bundle
@pytest.mark.parametrize("target", page.TARGETS, ids=[str(t) for t in page.TARGETS])
def test_published_page_matches_the_catalog(target):
    if not target.exists():
        pytest.skip(f"{target} not on this machine")
    assert target.read_text() == page.render(bundle=BUNDLE), "run: uv run scripts/build_practices_page.py"
