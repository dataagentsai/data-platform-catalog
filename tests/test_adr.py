"""ADR checks (D14): each row breaks one ADR in one way and names the error expected."""
import copy
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import adr_index  # noqa: E402
import lint  # noqa: E402
import lint_shape  # noqa: E402

ROOT = lint.ROOT
ADRS = lint_shape.load_adrs()
VOCAB = lint.load_vocab()
CAPS = {c["id"] for c in lint.load_capabilities()}
DAC = {r["id"] for r in lint.load_obligations()}
A = next(a for a in ADRS if a["id"] == "ADR-003")


def broken(**changes):
    a = copy.deepcopy(A)
    for k, v in changes.items():
        if v is None:
            a.pop(k, None)
        else:
            a[k] = v
    return a


CASES = [
    ("valid as written", broken(), None),
    ("no id", broken(id=None), "missing front matter 'id'"),
    ("bad id shape", broken(id="ADR-3"), "id must look like ADR-001"),
    ("file name not its id", broken(id="ADR-099"), "does not start with its id"),
    ("unknown status", broken(status="maybe"), "unknown status"),
    ("superseded with no successor", broken(status="superseded"), "superseded without a superseded_by"),
    ("unknown concern", broken(concerns=["X99"]), "unknown concern"),
    ("cites a missing capability", broken(dpc=["DPC-9999"]), "not a DPC capability"),
    ("cites a missing obligation", broken(dac=["ZZZ-01"]), "not a DAC obligation"),
    ("no considered options", broken(_body=A["_body"].replace("## Considered Options", "## Options")),
     "missing section '## Considered Options'"),
    ("product name in the text", broken(_body=A["_body"] + "\nWe use Snowflake."), "product name 'snowflake'"),
    ("product name in a source", broken(source=["the Databricks docs"]), "product name 'databricks'"),
]


@pytest.mark.parametrize("name,adr,error", CASES, ids=[c[0] for c in CASES])
def test_adr(name, adr, error):
    errs = lint_shape.lint_adrs([adr], VOCAB, CAPS, DAC)
    assert errs == [] if error is None else any(error in e for e in errs), errs


def test_every_adr_is_clean():
    readme = (ROOT / "adr" / "README.md").read_text()
    assert lint_shape.lint_adrs(ADRS, VOCAB, CAPS, DAC, readme) == []


def test_index_is_generated_and_current():
    readme = (ROOT / "adr" / "README.md").read_text()
    assert adr_index.with_index(readme, ADRS) == readme


def test_index_misses_a_new_adr():
    extra = broken(id="ADR-024", _file="ADR-024-x.md")
    errs = lint_shape.lint_adrs(ADRS + [extra], VOCAB, CAPS, DAC, (ROOT / "adr" / "README.md").read_text())
    assert any("index does not list ADR-024" in e for e in errs), errs


def test_capability_cites_unknown_adr():
    caps = [{"_file": "X1", "id": "DPC-0001", "adr": ["ADR-999"]}]
    assert lint_shape.lint_capability_adrs(caps, {a["id"] for a in ADRS}) == [
        "X1:DPC-0001: cites ADR-999, which is not an ADR"]


@pytest.mark.parametrize("brief_topic,adr_id", [
    ("silver source-aligned", "ADR-001"), ("pull straight to bronze", "ADR-002"), ("two gold pipeline kinds", "ADR-003"),
    ("hash surrogate keys, -1/-2", "ADR-004"), ("SCD2 as-of joins", "ADR-005"), ("facts as tables, MVs simple", "ADR-006"),
    ("13 standard stages", "ADR-007"), ("column projection all by default", "ADR-008"),
    ("DQ severity sets the action", "ADR-009"), ("metadata store behind stored procedures", "ADR-010"),
    ("clustering and automatic maintenance", "ADR-011"), ("catalog per environment and layer", "ADR-012"),
    ("IO only at the edges", "ADR-013"), ("two-layer binding (M1)", "ADR-014"),
    ("kernel/ports/adapters/realms (M2)", "ADR-015")])
def test_brief_decision_has_an_adr(brief_topic, adr_id):
    assert adr_id in {a["id"] for a in ADRS}, brief_topic
