# /// script
# requires-python = ">=3.9"
# dependencies = ["pyyaml", "jsonschema"]
# ///
"""Check layers/: the hard challenges and anti-patterns of each layer and hop. Exit 1 on any error.

    uv run scripts/lint_layers.py
"""
import re
import sys
from pathlib import Path

import yaml

from lint import ROOT, load_obligations
import lint_practices as lp

ORDER = ["source", "ingestion", "bronze", "bronze_to_silver", "silver", "silver_to_gold", "gold",
         "gold_to_semantic", "semantic", "semantic_to_ui"]
VERDICTS = {"solve", "assist", "people_decide"}
STATUSES = {"built", "building", "designed", "gap"}
COMPONENTS = {"contracts", "metadata_store", "puller", "lander", "silver_engine", "gold_harness", "des",
              "semantic_generators", "observability", "agents", "app"}
LAYER_KEYS = ["id", "order", "title", "purpose", "components", "challenges", "anti_patterns"]
CH_KEYS = ["id", "title", "goes_wrong", "example", "solution", "verdict", "status"]
CH_ID = re.compile(r"^[A-Z0-9]{2,4}-\d{2}$")
AP_ID = re.compile(r"^AP-[A-Z]{2,4}-\d{2}$")
NORMATIVE = ["title", "purpose", "goes_wrong", "solution", "why", "instead"]


def load_layers(root=ROOT):
    return [yaml.safe_load(f.read_text()) for f in sorted((root / "layers").glob("*.yaml"))]


def _r1(where, rec):
    return [f"{where}: product name '{p}' in {k} (rule R1)" for k in NORMATIVE for p in lp.products_in(rec.get(k))]


def lint_layers(layers, dac_ids, adrs, practices):
    errs, seen = [], set()
    ids = [x.get("id") for x in layers]
    if ids != ORDER:
        errs.append(f"layers must be exactly {ORDER} in that order, found {ids}")
    for i, lay in enumerate(layers, 1):
        lid = lay.get("id", f"#{i}")
        errs += [f"{lid}: missing {k}" for k in LAYER_KEYS if k not in lay]
        if lay.get("order") != i:
            errs.append(f"{lid}: order {lay.get('order')} should be {i}")
        errs += [f"{lid}: unknown component {c}" for c in lay.get("components") or [] if c not in COMPONENTS]
        errs += _r1(lid, lay)
        if not lay.get("challenges"):
            errs.append(f"{lid}: needs at least one challenge")
        for ch in lay.get("challenges") or []:
            cid = ch.get("id", "?")
            w = f"{lid}/{cid}"
            errs += [f"{w}: missing {k}" for k in CH_KEYS if not ch.get(k)]
            if not CH_ID.match(cid):
                errs.append(f"{w}: bad id")
            if cid in seen:
                errs.append(f"{w}: duplicate id")
            seen.add(cid)
            if ch.get("verdict") not in VERDICTS:
                errs.append(f"{w}: verdict must be one of {sorted(VERDICTS)}")
            if ch.get("status") not in STATUSES:
                errs.append(f"{w}: status must be one of {sorted(STATUSES)}")
            errs += [f"{w}: unknown DAC id {d}" for d in ch.get("dac") or [] if d not in dac_ids]
            errs += [f"{w}: unknown ADR {a}" for a in ch.get("adr") or [] if a not in adrs]
            errs += [f"{w}: unknown practice {p}" for p in ch.get("practices") or [] if p not in practices]
            day = ch.get("world_day")
            if day is not None and not (isinstance(day, int) and 1 <= day <= 14):
                errs.append(f"{w}: world_day must be a day of the 14-day world")
            if not (ch.get("dac") or ch.get("adr") or ch.get("practices")):
                errs.append(f"{w}: link at least one DAC id, ADR or practice")
            errs += _r1(w, ch)
        for ap in lay.get("anti_patterns") or []:
            if "practice" in ap:
                p = practices.get(ap["practice"])
                if p is None:
                    errs.append(f"{lid}: anti-pattern names unknown practice {ap['practice']}")
                elif p.get("kind") != "anti-pattern":
                    errs.append(f"{lid}: {ap['practice']} is not an anti-pattern")
            else:
                aid = ap.get("id", "?")
                if not AP_ID.match(aid) or aid in seen:
                    errs.append(f"{lid}/{aid}: new anti-pattern needs a unique AP-XXX-NN id")
                seen.add(aid)
                if ap.get("new") is not True:
                    errs.append(f"{lid}/{aid}: a new anti-pattern says new: true (reuse a practice where one fits)")
                errs += [f"{lid}/{aid}: missing {k}" for k in ("title", "why", "instead") if not ap.get(k)]
                errs += _r1(f"{lid}/{aid}", ap)
    return errs


def run(root=ROOT):
    layers = load_layers(root)
    dac_ids = {o["id"] for o in load_obligations(root)}
    practices = {p["id"]: p for p in lp.load_practices(root)}
    return lint_layers(layers, dac_ids, lp.adr_ids(root), practices), layers


def main():
    errs, layers = run()
    for e in errs:
        print("ERROR", e)
    chs = [c for x in layers for c in x.get("challenges") or []]
    aps = [a for x in layers for a in x.get("anti_patterns") or []]
    split = {v: sum(c.get("verdict") == v for c in chs) for v in sorted(VERDICTS)}
    print(f"Layers: {len(layers)}, challenges: {len(chs)} ({', '.join(f'{v} {k}' for k, v in split.items())}), "
          f"anti-patterns: {len(aps)} ({sum('practice' in a for a in aps)} reused, {sum('practice' not in a for a in aps)} new)")
    print(f"{len(errs)} errors")
    sys.exit(1 if errs else 0)


if __name__ == "__main__":
    main()
