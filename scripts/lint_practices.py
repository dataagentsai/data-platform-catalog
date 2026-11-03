# /// script
# requires-python = ">=3.9"
# dependencies = ["pyyaml", "jsonschema"]
# ///
"""Check practices/ and the enforced_by links on DAC obligations (goal G1, decision D12). Exit 1 on any error.

    uv run scripts/lint_practices.py

The shift-left bundle is read from $SHIFT_LEFT_BUNDLE, or ../shift-left-bundle next to this repository. Without it,
the checks that need the bundle are skipped and the run says so.
"""
import os
import re
import sys
from pathlib import Path

import yaml

from lint import PRODUCTS, ROOT, STATUSES, load_obligations, load_vocab

KINDS = {"principle", "practice", "anti-pattern"}
BINDINGS = {"aws-databricks"}          # bindings a `how` example may be written for
ENFORCE_KEYS = {"shift_left", "proposed", "runtime", "review"}
STAGES = {"commit", "pr", "predeploy", "nightly"}  # the bundle's stages
REQUIRED = ["id", "status", "since", "kind", "title", "why", "how", "layers", "components", "enforced_by", "dac"]
NORMATIVE = ["title", "why", "instead"]  # rule R1: no product names here
# Names from the AWS and Databricks binding that lint.PRODUCTS does not list. Checked on practices only.
MORE_PRODUCTS = ["genie", "macie", "photon", "aurora", "postgresql", "appflow", "eventbridge", "cloudtrail", "cloudwatch",
                 "sns", "privatelink", "kms", "dqx", "ruff", "lakehouse monitoring", "asset bundles", "sitewise",
                 "transfer family", "dms", "costsherlock", "datatwin", "liquid clustering", "predictive optimization",
                 "variant", "delta", "metric views", "metric view", "system tables"]
# Session B writes the ADRs. Until adr/ exists, a practice may name only these placeholder ids (from its brief).
ADR_PLACEHOLDERS = {f"ADR-{n:03d}" for n in range(1, 16)}
GAP_DEFAULT = "No build-time check yet: found only by the runtime test."


def bundle_dir():
    return Path(os.environ.get("SHIFT_LEFT_BUNDLE", ROOT.parent / "shift-left-bundle"))


def load_bundle(path=None):
    """The shift-left checks, {id: record}, or None when the bundle is not on this machine."""
    d = (path or bundle_dir()) / "catalog" / "checks"
    if not d.is_dir():
        return None
    return {c["id"]: c for f in sorted(d.glob("*.yaml")) for c in yaml.safe_load(f.read_text()) or []}


def load_practices(root=ROOT):
    recs = []
    for f in sorted((root / "practices").glob("*.yaml")):
        if f.stem in ("components", "proposed-checks", "dropped"):
            continue
        for r in yaml.safe_load(f.read_text()) or []:
            r["_file"] = f.stem
            recs.append(r)
    return sorted(recs, key=lambda r: r.get("id", ""))


def load_part(name, root=ROOT):
    return yaml.safe_load((root / "practices" / f"{name}.yaml").read_text()) or ([] if name != "components" else {})


def adr_ids(root=ROOT):
    d = root / "adr"
    if not d.is_dir():
        return ADR_PLACEHOLDERS
    return {m.group(0) for f in d.rglob("*") if f.is_file() for m in [re.search(r"ADR-\d{3}", f.name)] if m}


def products_in(text):
    low = (text or "").lower()
    return [p for p in PRODUCTS + MORE_PRODUCTS if re.search(rf"\b{re.escape(p)}\b", low)]


def lint_practices(recs, vocab, comps, dac_ids, proposed_ids, adrs, bundle_ids=None, dropped_ids=()):
    errs = []
    ids = [r.get("id") for r in recs] + list(dropped_ids)
    for r in recs:
        w = f"{r.get('_file', '?')}:{r.get('id', '?')}"
        for k in REQUIRED:
            if r.get(k) in (None, "", [], {}):
                errs.append(f"{w}: missing '{k}'")
        if r.get("id") and not re.match(r"^BP-\d{3}$", r["id"]):
            errs.append(f"{w}: id must look like BP-001")
        if ids.count(r.get("id")) > 1:
            errs.append(f"{w}: duplicate id")
        if r.get("status") and r["status"] not in STATUSES:
            errs.append(f"{w}: unknown status '{r['status']}'")
        kind = r.get("kind")
        if kind and kind not in KINDS:
            errs.append(f"{w}: kind must be principle, practice or anti-pattern")
        if kind == "anti-pattern" and not r.get("instead"):
            errs.append(f"{w}: an anti-pattern needs 'instead'")
        if kind in ("principle", "practice") and r.get("instead"):
            errs.append(f"{w}: only an anti-pattern has 'instead'")
        if r.get("_file") and kind in KINDS and r.get("components"):
            want = "canon" if kind == "principle" else r["components"][0]
            if r["_file"] != want:
                errs.append(f"{w}: belongs in practices/{want}.yaml")
        for s in r.get("layers") or []:
            if s not in vocab["stages"]:
                errs.append(f"{w}: unknown layer '{s}'")
        for c in r.get("components") or []:
            if c not in comps:
                errs.append(f"{w}: unknown component '{c}'")
        how = r.get("how") or {}
        if r.get("how") and (not isinstance(how, dict) or not how.get("text")):
            errs.append(f"{w}: 'how' needs a text")
        elif r.get("how") and how.get("binding") not in BINDINGS:
            errs.append(f"{w}: 'how' must name its binding, one of {sorted(BINDINGS)}")
        for d in r.get("dac") or []:
            if d not in dac_ids:
                errs.append(f"{w}: dac '{d}' is not a DAC obligation")
        for a in r.get("adr") or []:
            if a not in adrs:
                errs.append(f"{w}: adr '{a}' does not exist")
        for e in r.get("enforced_by") or []:
            if not isinstance(e, dict) or len(e) != 1 or next(iter(e)) not in ENFORCE_KEYS:
                errs.append(f"{w}: enforced_by entry {e!r} must be one of {sorted(ENFORCE_KEYS)}")
                continue
            k, v = next(iter(e.items()))
            if not v:
                errs.append(f"{w}: enforced_by {k} is empty")
            if k == "proposed" and v not in proposed_ids:
                errs.append(f"{w}: proposed check '{v}' is not in practices/proposed-checks.yaml")
            if k == "shift_left" and bundle_ids is not None:
                errs += [f"{w}: shift-left check '{i}' is not in the bundle" for i in v if i not in bundle_ids]
        for k in NORMATIVE:
            for p in products_in(r.get(k)):
                errs.append(f"{w}: product name '{p}' in {k}")
    return errs


def lint_proposed(proposed, dac_ids, used, bundle_ids=None):
    errs, ids = [], [p.get("id") for p in proposed]
    for p in proposed:
        w = f"proposed {p.get('id', '?')}"
        for k in ("id", "title", "stage", "catches", "dac"):
            if not p.get(k):
                errs.append(f"{w}: missing '{k}'")
        if p.get("id") and not re.match(r"^SL-[A-Z]+(-[A-Z]+)?-\d{2}$", p["id"]):
            errs.append(f"{w}: id must look like SL-AREA-01")
        if ids.count(p.get("id")) > 1:
            errs.append(f"{w}: duplicate id")
        if p.get("stage") and p["stage"] not in STAGES:
            errs.append(f"{w}: stage must be one of {sorted(STAGES)}")
        errs += [f"{w}: dac '{d}' is not a DAC obligation" for d in p.get("dac") or [] if d not in dac_ids]
        if bundle_ids is not None and p.get("id") in bundle_ids:
            errs.append(f"{w}: the bundle has this check now; delete it from proposed-checks.yaml")
        if p.get("id") not in used:
            errs.append(f"{w}: no practice uses it (orphan)")
    return errs


def expected_enforced(obligations, bundle, proposed):
    """Per DAC id, the shift-left and proposed checks that name it: the reverse of their `dac:` links."""
    out = {r["id"]: {"shift_left": set(), "proposed": set()} for r in obligations}
    for c in (bundle or {}).values():
        for d in c.get("dac") or []:
            if d in out:
                out[d]["shift_left"].add(c["id"])
    for p in proposed:
        for d in p.get("dac") or []:
            if d in out:
                out[d]["proposed"].add(p["id"])
    return {k: {kk: sorted(vv) for kk, vv in v.items()} for k, v in out.items()}


def lint_enforced_by(obligations, bundle, proposed):
    errs = []
    want = expected_enforced(obligations, bundle, proposed)
    proposed_ids = {p["id"] for p in proposed}
    for r in obligations:
        w = f"{r.get('_file', '?')}:{r['id']}"
        e = r.get("enforced_by")
        if not isinstance(e, dict):
            errs.append(f"{w}: missing 'enforced_by'")
            continue
        missing = {"shift_left", "proposed", "runtime", "review", "gap"} - set(e)
        if missing:
            errs.append(f"{w}: enforced_by lacks {sorted(missing)}")
            continue
        if bundle is not None and e["shift_left"] != want[r["id"]]["shift_left"]:
            errs.append(f"{w}: enforced_by.shift_left is out of date; run scripts/enforced_by.py")
        elif bundle is None and any(not re.match(r"^SL-", i) for i in e["shift_left"]):
            errs.append(f"{w}: enforced_by.shift_left holds a non-check id")
        if e["proposed"] != want[r["id"]]["proposed"]:
            errs.append(f"{w}: enforced_by.proposed is out of date; run scripts/enforced_by.py")
        errs += [f"{w}: proposed check '{i}' does not exist" for i in e["proposed"] if i not in proposed_ids]
        if not isinstance(e["runtime"], bool):
            errs.append(f"{w}: enforced_by.runtime must be true or false")
        if e["runtime"] and not r.get("test"):
            errs.append(f"{w}: runtime is true but the obligation has no test")
        if not (e["shift_left"] or e["proposed"] or e["runtime"] or e["review"]):
            errs.append(f"{w}: nothing enforces it")
        if not (e["shift_left"] or e["proposed"]) and not e["gap"]:
            errs.append(f"{w}: no build-time check, so 'gap' must say so")
    return errs


def warnings(practices, obligations, bundle):
    """Not errors: a practice citing a check whose DAC links it does not share, and obligations no practice serves."""
    out = []
    for r in practices:
        for e in r.get("enforced_by") or []:
            for i in e.get("shift_left", []) if isinstance(e, dict) else []:
                linked = set((bundle or {}).get(i, {}).get("dac") or [])
                if linked and not linked & set(r.get("dac") or []):
                    out.append(f"{r['id']}: cites {i} (serves {sorted(linked)}) but links none of those")
    served = {d for r in practices for d in r.get("dac") or []}
    out += [f"{o['id']}: no practice serves it" for o in obligations if o["id"] not in served]
    return out


def run(root=ROOT, bundle=None):
    vocab, obligations = load_vocab(root), load_obligations(root)
    practices, proposed = load_practices(root), load_part("proposed-checks", root)
    dropped, comps = load_part("dropped", root), load_part("components", root)
    dac_ids = {o["id"] for o in obligations}
    used = {e["proposed"] for r in practices for e in r.get("enforced_by") or [] if isinstance(e, dict) and "proposed" in e}
    bundle_ids = set(bundle) if bundle is not None else None
    errs = lint_practices(practices, vocab, comps, dac_ids, {p["id"] for p in proposed}, adr_ids(root), bundle_ids,
                          [d["id"] for d in dropped])
    errs += lint_proposed(proposed, dac_ids, used, bundle_ids)
    errs += [f"dropped {d.get('id')}: needs a reason" for d in dropped if not d.get("dropped")]
    errs += lint_enforced_by(obligations, bundle, proposed)
    return errs, warnings(practices, obligations, bundle), practices, obligations, dropped


def main():
    bundle = load_bundle()
    errs, warns, practices, obligations, dropped = run(bundle=bundle)
    for e in errs:
        print("ERROR", e)
    for x in warns:
        print("note ", x)
    if bundle is None:
        print(f"note  shift-left bundle not found at {bundle_dir()}: bundle checks skipped")
    kinds = {k: sum(r["kind"] == k for r in practices) for k in sorted(KINDS)}
    build = sum(bool(o["enforced_by"]["shift_left"] or o["enforced_by"]["proposed"])
                for o in obligations if isinstance(o.get("enforced_by"), dict))
    print(f"Practices: {len(practices)} ({', '.join(f'{v} {k}' for k, v in kinds.items())}), {len(dropped)} dropped.")
    print(f"DAC: {build} of {len(obligations)} obligations have a build-time check (shift-left or proposed).")
    print(f"{len(errs)} errors, {len(warns)} notes")
    sys.exit(1 if errs else 0)


if __name__ == "__main__":
    main()
