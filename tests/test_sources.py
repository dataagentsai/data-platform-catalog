"""Source families and profiles: the shipped files pass, and each row below breaks them in one way."""
import copy
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import lint_sources as ls  # noqa: E402

FAM, PROF = ls.load()


def fam_with(fn):
    f = copy.deepcopy(FAM)
    fn(f)
    return f


def prof_with(fn):
    p = copy.deepcopy(PROF)
    fn(p)
    return p


def test_the_shipped_files_pass():
    assert ls.check_families(FAM) == []
    assert ls.check_profiles(PROF, FAM) == []


def test_every_family_has_a_route_and_every_route_a_family():
    used = {r["family"] for p in PROF["products"] for r in p["routes"]}
    assert used == {f["id"] for f in FAM["families"]}


@pytest.mark.parametrize(
    ("case", "edit", "expect"),
    [
        ("a product name in normative text", lambda f: f["families"][0].__setitem__("approach", "Use Snowflake for it"), "product name"),
        ("an unknown arrival shape", lambda f: f["families"][0].__setitem__("arrival", "pigeons"), "arrival"),
        ("a missing question", lambda f: f["families"][1]["questions"].pop("deletes"), "question deletes"),
        ("an unknown capability", lambda f: f["families"][2].__setitem__("needs", ["magic"]), "not a capability"),
        ("a repeated id", lambda f: f["families"][1].__setitem__("id", "F1"), "repeated"),
        ("no contract test", lambda f: f["families"][3].__setitem__("contract_test", ""), "contract_test is missing"),
    ],
)
def test_family_rules(case, edit, expect):
    errs = ls.check_families(fam_with(edit))
    assert any(expect in e for e in errs), (case, errs)


@pytest.mark.parametrize(
    ("case", "edit", "expect"),
    [
        ("an unknown family", lambda p: p["products"][0]["routes"][0].__setitem__("family", "F99"), "not a family"),
        ("an unknown capability", lambda p: p["products"][0]["routes"][0].__setitem__("capabilities", ["x"]), "unknown"),
        ("a level off the scale", lambda p: p["products"][0]["routes"][0].__setitem__("proof_level", 7), "not on the scale"),
        ("level 4 claimed", lambda p: p["products"][0]["routes"][0].__setitem__("proof_level", 4), "claims production hardening"),
        ("level 2 with no evidence", lambda p: p["products"][0]["routes"][0].update(proof_level=2, evidence="none"), "needs evidence"),
        ("verified not a boolean", lambda p: p["products"][0]["routes"][0].__setitem__("verified", "yes"), "verified"),
        ("a product with no policy", lambda p: p["products"][1].__setitem__("policy", ""), "policy is missing"),
        ("a repeated product", lambda p: p["products"][1].__setitem__("id", p["products"][0]["id"]), "repeated"),
    ],
)
def test_profile_rules(case, edit, expect):
    errs = ls.check_profiles(prof_with(edit), FAM)
    assert any(expect in e for e in errs), (case, errs)


def test_sap_routes_name_the_certified_route_policy():
    sap = next(p for p in PROF["products"] if p["id"] == "sap")
    assert "certif" in sap["policy"].lower()
    assert {r["family"] for r in sap["routes"]} >= {"F5", "F6", "F1", "F3"}, "SAP offers routes in several families"
