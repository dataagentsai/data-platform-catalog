"""Lint the source families (dpc/source_families.yaml, product-free) and the source profiles
(dbs/sources/source_profiles.yaml, products allowed). Used by tests/test_sources.py and `python scripts/lint_sources.py`.

Rules:
  families   product-free text (R1); every family has its five questions, an approach, a fallback, a contract test; its
             arrival shape, initiators and needs come from the closed vocabularies in the same file
  profiles   every route names a known family and only known capabilities; a proof level from the file's scale; a route at
             level 2 or above must have evidence; a route may not claim level 4 until one is hardened; a product has a policy
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
import lint  # noqa: E402

QUESTIONS = ("changes", "deletes", "order_and_repeats", "who_starts", "what_arrives")
FAMILY_KEYS = ("id", "name", "arrival", "initiators", "questions", "approach", "needs", "fallback", "contract_test")
ROUTE_KEYS = ("name", "family", "capabilities", "proof_level", "verified", "evidence", "constraint")
MAX_PROOF_TODAY = 3  # no route has been hardened for production yet


def load(root: Path = ROOT):
    fam = yaml.safe_load((root / "dpc/source_families.yaml").read_text())
    prof = yaml.safe_load((root / "dbs/sources/source_profiles.yaml").read_text())
    return fam, prof


def text_of(value) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [t for v in value.values() for t in text_of(v)]
    if isinstance(value, list):
        return [t for v in value for t in text_of(v)]
    return []


def check_families(fam: dict) -> list[str]:
    errs: list[str] = []
    shapes, inits, caps = set(fam["arrival_shapes"]), set(fam["initiators"]), set(fam["capabilities"])
    seen: set[str] = set()
    for f in fam["families"]:
        fid = f.get("id", "?")
        for k in FAMILY_KEYS:
            if not f.get(k):
                errs.append(f"{fid}: {k} is missing")
        if fid in seen:
            errs.append(f"{fid}: id repeated")
        seen.add(fid)
        if f.get("arrival") not in shapes:
            errs.append(f"{fid}: arrival {f.get('arrival')!r} is not one of {sorted(shapes)}")
        errs += [f"{fid}: initiator {i!r} is unknown" for i in f.get("initiators", []) if i not in inits]
        errs += [f"{fid}: need {c!r} is not a capability" for c in f.get("needs", []) if c not in caps]
        errs += [f"{fid}: question {q} is missing" for q in QUESTIONS if q not in (f.get("questions") or {})]
    for t in text_of(fam):
        errs += [f"families: product name {p!r} in normative text" for p in lint.products_in(t)]
    return sorted(set(errs))


def check_profiles(prof: dict, fam: dict) -> list[str]:
    errs: list[str] = []
    fam_ids = {f["id"] for f in fam["families"]}
    caps = set(fam["capabilities"])
    levels = set(fam["proof_levels"])
    seen: set[str] = set()
    for p in prof["products"]:
        pid = p.get("id", "?")
        if pid in seen:
            errs.append(f"{pid}: id repeated")
        seen.add(pid)
        if not p.get("policy"):
            errs.append(f"{pid}: policy is missing")
        if not p.get("routes"):
            errs.append(f"{pid}: no routes")
        for r in p.get("routes", []):
            where = f"{pid} / {r.get('name', '?')}"
            errs += [f"{where}: {k} is missing" for k in ROUTE_KEYS if k not in r]
            if r.get("family") not in fam_ids:
                errs.append(f"{where}: family {r.get('family')!r} is not a family")
            errs += [f"{where}: capability {c!r} is unknown" for c in r.get("capabilities", []) if c not in caps]
            lvl = r.get("proof_level")
            if lvl not in levels:
                errs.append(f"{where}: proof level {lvl!r} is not on the scale")
            elif lvl > MAX_PROOF_TODAY:
                errs.append(f"{where}: level {lvl} claims production hardening that no route has")
            elif lvl >= 2 and str(r.get("evidence", "none")).lower() in ("", "none"):
                errs.append(f"{where}: level {lvl} needs evidence")
            if not isinstance(r.get("verified"), bool):
                errs.append(f"{where}: verified must be true or false")
    return sorted(set(errs))


def main() -> int:
    fam, prof = load()
    errs = check_families(fam) + check_profiles(prof, fam)
    for e in errs:
        print(e)
    if not errs:
        n = sum(len(p["routes"]) for p in prof["products"])
        print(f"{len(fam['families'])} families, {len(prof['products'])} products, {n} routes: ok")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
