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
