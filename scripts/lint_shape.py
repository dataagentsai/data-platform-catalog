# /// script
# requires-python = ">=3.9"
# dependencies = ["pyyaml", "jsonschema"]
# ///
"""Checks for the Goal 1b shape work (session B): ADRs, the deck crosswalk, two-layer DBS (engine + cloud, composed
by stacks), the DPM v0.2 kinds (dataset blocks, gold, metric, ML model, platform) and DWD worlds.

Called from scripts/lint.py; also runnable alone:

    uv run scripts/lint_shape.py
"""
import json
import re
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lint  # noqa: E402

ROOT = lint.ROOT


def _y(p):
    return yaml.safe_load(Path(p).read_text())


def _validator(schema_dir, name):
    """A validator for one schema file that resolves relative $refs to its sibling schema files."""
    from jsonschema import Draft202012Validator
    from referencing import Registry, Resource
    schemas = [json.loads(f.read_text()) for f in Path(schema_dir).glob("*.schema.json")]
    reg = Registry().with_resources([(s["$id"], Resource.from_contents(s)) for s in schemas])
    main = next(s for s in schemas if s["$id"].endswith("/" + name))
    return Draft202012Validator(main, registry=reg)


def _schema_errors(validator, doc, where):
    return [f"{where}: {'/'.join(map(str, e.path)) or '(top)'}: {e.message}"
            for e in sorted(validator.iter_errors(doc), key=lambda e: list(e.path))]


# ---------------------------------------------------------------- ADRs (D14)
ADR_STATUSES = {"proposed", "accepted", "deprecated", "superseded"}
ADR_FIELDS = ["id", "status", "date", "decision-makers", "concerns", "dpc", "dac", "plan", "source"]
ADR_SECTIONS = ["## Context and Problem Statement", "## Considered Options", "## Decision Outcome", "### Consequences"]


def load_adrs(root=ROOT):
    out = []
    for f in sorted((root / "adr").glob("ADR-*.md")):
        text = f.read_text()
        m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
        fm = (yaml.safe_load(m.group(1)) or {}) if m else {}
        body = m.group(2) if m else text
        title = next((ln[2:].split(" ", 1)[1] for ln in body.splitlines() if ln.startswith("# ")), "")
        out.append({**fm, "_file": f.name, "_body": body, "_title": title})
    return out


def lint_adrs(adrs, vocab, cap_ids, dac_ids, readme=None):
    errs, ids = [], [a.get("id") for a in adrs]
    for a in adrs:
        w = f"adr/{a['_file']}"
        for k in ADR_FIELDS:
            if a.get(k) in (None, ""):
                errs.append(f"{w}: missing front matter '{k}'")
        if a.get("id") and not re.match(r"^ADR-\d{3}$", a["id"]):
            errs.append(f"{w}: id must look like ADR-001")
        if a.get("id") and not a["_file"].startswith(a["id"] + "-"):
            errs.append(f"{w}: file name does not start with its id {a['id']}")
        if ids.count(a.get("id")) > 1:
            errs.append(f"{w}: duplicate id")
        if a.get("status") and a["status"] not in ADR_STATUSES:
            errs.append(f"{w}: unknown status '{a['status']}'")
        if a.get("status") == "superseded" and a.get("superseded_by") not in ids:
            errs.append(f"{w}: superseded without a superseded_by that exists")
        errs += [f"{w}: missing section '{s}'" for s in ADR_SECTIONS if s not in a["_body"]]
        errs += [f"{w}: unknown concern '{c}'" for c in a.get("concerns") or [] if c not in vocab["concerns"]]
        errs += [f"{w}: cites {c}, which is not a DPC capability" for c in a.get("dpc") or [] if c not in cap_ids]
        errs += [f"{w}: cites {d}, which is not a DAC obligation" for d in a.get("dac") or [] if d not in dac_ids]
        errs += [f"{w}: product name '{p}'" for p in lint.products_in(a["_body"] + " " + " ".join(a.get("source") or []))]
    if readme is not None:
        errs += [f"adr/README.md: index does not list {a['id']}" for a in adrs if f"[{a['id']}]" not in readme]
    return errs


def lint_capability_adrs(caps, adr_ids):
    return [f"{c['_file']}:{c['id']}: cites {a}, which is not an ADR" for c in caps for a in c.get("adr") or []
            if a not in adr_ids]


# ---------------------------------------------------------------- deck crosswalk (D13)
DECK_IDS = [f"C{i:02d}" for i in range(1, 69)]


def lint_crosswalk(cw, vocab, cap_ids, port_names, name="crosswalks/deck.yaml"):
    errs, rows = [], cw.get("concerns") or []
    seen = [r.get("deck") for r in rows]
    errs += [f"{name}: deck concern {c} is missing" for c in DECK_IDS if c not in seen]
    errs += [f"{name}: deck concern {c} is listed {seen.count(c)} times" for c in set(seen) if seen.count(c) > 1]
    errs += [f"{name}: '{c}' is not a deck concern id" for c in seen if c not in DECK_IDS]
    for r in rows:
        w = f"{name}:{r.get('deck')}"
        for k in ("name", "group", "lead", "concerns", "dpc", "ports"):
            if r.get(k) is None:
                errs.append(f"{w}: missing '{k}'")
        if not r.get("dpc"):
            errs.append(f"{w}: no DPC capability (an unmapped deck concern)")
        if r.get("lead") not in ("X", "Y", "Z"):
            errs.append(f"{w}: lead must be X, Y or Z")
        errs += [f"{w}: unknown concern '{c}'" for c in r.get("concerns") or [] if c not in vocab["concerns"]]
        errs += [f"{w}: {c} is not a DPC capability" for c in r.get("dpc") or [] if c not in cap_ids]
        errs += [f"{w}: {p} is not a port" for p in r.get("ports") or [] if p not in port_names]
        errs += [f"{w}: product name '{p}'" for p in lint.products_in(f"{r.get('name')} {r.get('note', '')}")]
    return errs


# ---------------------------------------------------------------- DBS: layers and stacks (M1, ADR-014)
def load_layers(root=ROOT):
    return {(d.name, f.stem): _y(f) for d in (root / "dbs").iterdir() if d.name in ("engine", "cloud")
            for f in sorted(d.glob("*.yaml"))}


def load_stacks(root=ROOT):
    return {f.stem: _y(f) for f in sorted((root / "dbs" / "stacks").glob("*.yaml"))}


def _layer_view(layer, profile=None):
    """A layer's bindings, decisions, thresholds and gaps with one profile applied."""
    b = dict(layer.get("bindings") or {})
    dec, thr = dict(layer.get("decisions") or {}), dict(layer.get("thresholds") or {})
    gaps = list(layer.get("accepted_gaps") or [])
    if profile:
        p = (layer.get("profiles") or {})[profile]
        for port in p.get("unbind") or []:
            b.pop(port, None)
        b.update(p.get("bindings") or {})
        dec.update(p.get("decisions") or {})
        thr.update(p.get("thresholds") or {})
        gaps += p.get("accepted_gaps") or []
    return b, dec, thr, gaps


def compose(stack, layers):
    """Engine + cloud + profile -> one binding in the binding.schema.json (v0.1) shape. Generated, never stored."""
    eng = layers[("engine", stack["engine"]["layer"])]
    eb, ed, et, eg = _layer_view(eng, stack["engine"].get("profile"))
    cb, cd, ct, cg = ({}, {}, {}, [])
    if stack.get("cloud"):
        cb, cd, ct, cg = _layer_view(layers[("cloud", stack["cloud"]["layer"])], stack["cloud"].get("profile"))
    bindings = {}
    for port in sorted(set(eb) | set(cb)):
        if port in eb and port in cb:
            win, lose = (eb, cb) if stack["prefer"].get(port, "engine") == "engine" else (cb, eb)
            chosen = json.loads(json.dumps(win[port]))
            chosen.setdefault("settings", {})["also_bound_by_other_layer"] = lose[port]["adapter"]
            bindings[port] = chosen
        else:
            bindings[port] = (eb.get(port) or cb.get(port))
    gaps, seen = [], set()
    for g in eg + cg + (stack.get("accepted_gaps") or []):
        if g["obligation"] not in seen:
            seen.add(g["obligation"])
            gaps.append(g)
    return {"apiVersion": "data-binding/v0.1",
            "subject": stack["subject"],
            "catalog": eng["catalog"],
            "decisions": {**ed, **cd, **(stack.get("decisions") or {})},
            "thresholds": {**et, **ct},
            "bindings": bindings,
            "accepted_gaps": gaps}


def lint_layer(key, layer, validator, ports, dac_ids):
    kind, name = key
    w = f"dbs/{kind}/{name}.yaml"
    errs = _schema_errors(validator, layer, w)
    if errs:
        return errs
    if layer["layer"] != kind:
        errs.append(f"{w}: says layer {layer['layer']} but lives in dbs/{kind}/")
    if layer["name"] != name:
        errs.append(f"{w}: name {layer['name']} does not match the file name")
    by = {p["port"]: p for p in ports}
    views = [("", layer.get("bindings") or {}, layer.get("accepted_gaps") or [])]
    for pn, p in (layer.get("profiles") or {}).items():
        views.append((f" profile {pn}", p.get("bindings") or {}, p.get("accepted_gaps") or []))
        errs += [f"{w} profile {pn}: unbinds {u}, which the base does not bind" for u in p.get("unbind") or []
                 if u not in (layer.get("bindings") or {})]
    for where, bindings, gaps in views:
        for port, b in bindings.items():
            if port not in by:
                errs.append(f"{w}{where}: binds '{port}', which is not a port in dpc/ports.yaml")
                continue
            if kind not in by[port].get("binds_in", []):
                errs.append(f"{w}{where}: port {port} may be bound by {by[port].get('binds_in')}, not by the {kind} layer")
            errs += [f"{w}{where}: {port} proves {i}, which is not a DAC obligation" for i in b["proves"] if i not in dac_ids]
        errs += [f"{w}{where}: accepted gap {g['obligation']} is not a DAC obligation" for g in gaps
                 if g["obligation"] not in dac_ids]
    return errs


def lint_stack(name, stack, validator, layers, binding_schema, port_names, dac_ids):
    w = f"dbs/stacks/{name}.yaml"
    errs = _schema_errors(validator, stack, w)
    if errs:
        return errs
    if stack["name"] != name:
        errs.append(f"{w}: name {stack['name']} does not match the file name")
    ek, ck = ("engine", stack["engine"]["layer"]), (("cloud", stack["cloud"]["layer"]) if stack.get("cloud") else None)
    if ek not in layers:
        return errs + [f"{w}: no engine layer dbs/engine/{ek[1]}.yaml"]
    if ck and ck not in layers:
        return errs + [f"{w}: no cloud layer dbs/cloud/{ck[1]}.yaml"]
    for k, side in ((ek, "engine"), (ck, "cloud")):
        prof = (stack.get(side) or {}).get("profile")
        if k and prof and prof not in (layers[k].get("profiles") or {}):
            errs.append(f"{w}: {side} layer {k[1]} has no profile '{prof}'")
    if errs:
        return errs
    eb = _layer_view(layers[ek], stack["engine"].get("profile"))[0]
    cb = _layer_view(layers[ck], stack["cloud"].get("profile"))[0] if ck else {}
    both = set(eb) & set(cb)
    errs += [f"{w}: both layers bind {p}; say which wins under prefer" for p in sorted(both - set(stack["prefer"]))]
    errs += [f"{w}: prefer names {p}, which only one layer binds" for p in sorted(set(stack["prefer"]) - both)]
    errs += lint.lint_binding(compose(stack, layers), binding_schema, port_names, dac_ids, f"{w} (composed)")
    return errs


def lint_dbs(root=ROOT, ports=None, dac_ids=None):
    ports = ports if ports is not None else lint.load_ports(root)
    dac_ids = dac_ids if dac_ids is not None else {r["id"] for r in lint.load_obligations(root)}
    sdir = root / "dbs" / "schema"
    lv, sv = _validator(sdir, "layer.schema.json"), _validator(sdir, "stack.schema.json")
    bschema = json.loads((sdir / "binding.schema.json").read_text())
    layers = load_layers(root)
    errs = []
    for k, layer in layers.items():
        errs += lint_layer(k, layer, lv, ports, dac_ids)
    for n, s in load_stacks(root).items():
        errs += lint_stack(n, s, sv, layers, bschema, {p["port"] for p in ports}, dac_ids)
    return errs


# ---------------------------------------------------------------- DPM v0.2 (D15) and DWD
SEVERITIES = {"critical", "major", "minor"}
SEVERITY_ALIASES = {"error": "critical", "warning": "minor"}   # ODCS examples, accepted so slice 1 stays valid
HISTORY_DEFAULT = {"master": "scd2", "transaction": "scd1", "event": "append", "snapshot": "snapshot"}
HISTORY_PATTERNS = {"scd2": {"history"}, "scd1": {"upsert", "history"}, "append": {"append"},
                    "snapshot": {"overwrite_window", "append"}}
INGEST_ARCHETYPES = {"push": {"PA1", "PA2"}, "pull": {"PA2", "PA3"}, "stream": {"PA4"}}
STORIES = {"late_data", "resend", "schema_change", "deletes", "out_of_order", "mass_delete", "correction",
           "late_dimension", "recon_mismatch"}


def contract_columns(contract):
    return {p["name"] for s in contract.get("schema", []) for p in s.get("properties", [])}


def contract_severities(contract):
    out = set()
    for s in contract.get("schema", []):
        for q in s.get("quality", []) or []:
            out.add(q.get("severity"))
        for p in s.get("properties", []):
            for q in p.get("quality", []) or []:
                out.add(q.get("severity"))
    return {x for x in out if x}


def lint_dataset_v02(m, contract, platform, name):
    """The rules DPM v0.2 adds for datasets, beyond lint.lint_manifest."""
    errs, cols = [], contract_columns(contract)
    h = m.get("history")
    if h:
        typ = h.get("type") or HISTORY_DEFAULT[h["kind"]]
        if m["load"]["pattern"] not in HISTORY_PATTERNS[typ]:
            errs.append(f"{name}: history {typ} does not fit load pattern {m['load']['pattern']}")
        errs += [f"{name}: history.track_columns uses '{c}', which is not a contract column"
                 for c in h.get("track_columns") or [] if c not in cols]
        if h.get("track_columns") and typ != "scd2":
            errs.append(f"{name}: track_columns only applies to history scd2, not {typ}")
    ing = m.get("ingest")
    if ing:
        if not set(m["archetypes"]) & INGEST_ARCHETYPES[ing["mode"]]:
            errs.append(f"{name}: ingest {ing['mode']} needs one of archetypes {sorted(INGEST_ARCHETYPES[ing['mode']])}")
        if ing["mode"] in ("pull", "stream") and "landing" in m["reconciliation"]["hops"]:
            errs.append(f"{name}: a {ing['mode']} dataset has no landing hop (ADR-002)")
        if ing.get("read") == "full_copy" and m["load"]["deletes"]["detect"] == "none":
            errs.append(f"{name}: a full copy must detect deletes by key_compare")
    if m["load"].get("mass_delete_max_share") is not None and (ing or {}).get("read") != "full_copy":
        errs.append(f"{name}: mass_delete_max_share applies only to full copies")
    actions = set(((m.get("quality") or {}).get("actions") or {})) | set((platform or {}).get("quality_defaults") or {})
    for sv in contract_severities(contract):
        sv2 = SEVERITY_ALIASES.get(sv, sv)
        if sv2 not in SEVERITIES:
            errs.append(f"{name}: contract severity '{sv}' is not critical, major or minor (ADR-009)")
        elif platform is not None and sv2 not in actions:
            errs.append(f"{name}: no action for severity '{sv2}'")
    for e in (m["reconciliation"].get("entries") or []):
        if e["left"] == e["right"]:
            errs.append(f"{name}: reconciliation entry {e['name']} compares {e['left']} with itself")
        used = list(e.get("keys") or []) + [x.get("column") for x in e["measures"]] + [(e.get("window") or {}).get("column")]
        errs += [f"{name}: reconciliation entry {e['name']} uses '{c}', which is not a contract column"
                 for c in used if c and c not in cols]
        errs += [f"{name}: reconciliation entry {e['name']} has no tolerance for {x['name']}"
                 for x in e["measures"] if x["name"] not in e["tolerance"]]
        errs += [f"{name}: reconciliation entry {e['name']} sums {x['name']} with no column"
                 for x in e["measures"] if x["agg"] != "count" and not x.get("column")]
    return errs


def lint_gold(g, contract, datasets, dims, name, input_cols):
    errs, cols = [], contract_columns(contract)
    if str(g["contract_version"]) != str(contract.get("version")):
        errs.append(f"{name}: pins contract {g['contract_version']} but the contract is {contract.get('version')}")
    used = [("grain", c) for c in g["grain"]] + [("window", (g.get("window") or {}).get("column"))]
    for d in g.get("dimensions") or []:
        used += [("dimension key", d["key"])] + [("dimension business key", c) for c in d["business_key"]]
    for m in ((g.get("checks") or {}).get("reconcile") or {}).get("measures") or []:
        used.append(("reconcile measure", m["column"]))
    errs += [f"{name}: {where} uses '{c}', which is not a contract column" for where, c in used if c and c not in cols]
    for d in g.get("dimensions") or []:
        if d.get("as_of") and d["as_of"] not in cols | input_cols:
            errs.append(f"{name}: as_of '{d['as_of']}' is in neither the contract nor an input's contract")
        if d["name"] not in dims:
            errs.append(f"{name}: dimension {d['name']} has no gold_dimension manifest")
    errs += [f"{name}: input {i['dataset']} has no dataset manifest in this domain" for i in g["inputs"]
             if i["dataset"] not in datasets]
    if g["pipeline"] == "one_to_one":
        if g.get("build"):
            errs.append(f"{name}: a one_to_one table has no build(); the common pipeline builds it (ADR-003)")
        if len(g["inputs"]) != 1:
            errs.append(f"{name}: a one_to_one table has exactly one input")
    if g["materialize"] == "materialized_view" and (len(g["inputs"]) > 1 or g.get("corrections")):
        errs.append(f"{name}: a materialized view only for a single-input aggregate without corrections (ADR-006)")
    if g["kind"] == "gold_dimension" and g["pipeline"] != "one_to_one":
        errs.append(f"{name}: dimensions are built by the common pipeline (one_to_one)")
    if g["kind"] == "gold_fact" and g["pipeline"] == "modelled" and not (g.get("checks") or {}).get("grain_unique"):
        errs.append(f"{name}: a modelled fact checks its grain is unique before publish")
    return errs


def lint_metric(mv, facts, dims, name):
    errs = []
    if mv["source"] not in facts:
        errs.append(f"{name}: source {mv['source']} has no gold_fact manifest")
    errs += [f"{name}: joins {j}, which has no gold_dimension manifest" for j in mv.get("joins") or [] if j not in dims]
    dnames = {d["name"] for d in mv["dimensions"]}
    for ms in mv["measures"]:
        if ms["time_dimension"] not in dnames:
            errs.append(f"{name}: measure '{ms['name']}' has time dimension '{ms['time_dimension']}', which is not a dimension")
        if ms["certification"] == "certified" and not ms.get("known_answer"):
            errs.append(f"{name}: certified measure '{ms['name']}' has no known-answer test (ADR-022)")
        if ms["certification"] == "certified" and not ms.get("synonyms"):
            errs.append(f"{name}: certified measure '{ms['name']}' has no synonyms")
    return errs


def lint_model(md, gold_cols, name):
    errs = []
    sources = [("target", md["target"]["source"], [md["target"]["column"]])]
    sources += [("feature", f["source"], f["columns"]) for f in md["features"]]
    for kind, src, columns in sources:
        if src not in gold_cols:
            errs.append(f"{name}: {kind} source {src} is not a gold table in this domain")
            continue
        errs += [f"{name}: {kind} column {src}.{c} is not in its contract" for c in columns if c not in gold_cols[src]]
    if md["target"]["source"] in gold_cols and md["training"]["as_of"] not in gold_cols[md["target"]["source"]]:
        errs.append(f"{name}: training as_of '{md['training']['as_of']}' is not a column of the target's source")
    return errs


def lint_world(world, datasets, cap_by_id, dac_ids, name, required_stories=None):
    errs = []
    if world.get("apiVersion") != "dwd/v0":
        errs.append(f"{name}: apiVersion must be dwd/v0")
    days = (world.get("clock") or {}).get("days", 0)
    system_ds = {d for s in (world.get("systems") or {}).values() for d in s.get("datasets") or []}
    errs += [f"{name}: system dataset {d} has no manifest" for d in sorted(system_ds - set(datasets))]
    ids = [e.get("id") for e in world.get("calendar") or []]
    for e in world.get("calendar") or []:
        w = f"{name}:{e.get('id')}"
        if ids.count(e.get("id")) > 1:
            errs.append(f"{w}: duplicate incident id")
        if not 1 <= e.get("day", 0) <= days:
            errs.append(f"{w}: day {e.get('day')} is outside the clock's {days} days")
        if e.get("story") and e["story"] not in STORIES:
            errs.append(f"{w}: unknown story '{e['story']}'")
        if e.get("dataset") and e["dataset"] not in system_ds:
            errs.append(f"{w}: dataset {e['dataset']} is not delivered by any system")
        ex = e.get("expect") or {}
        if ex.get("detector") not in dac_ids:
            errs.append(f"{w}: detector {ex.get('detector')} is not a DAC obligation")
        caps = [cap_by_id.get(c) for c in ex.get("handled_by") or []]
        errs += [f"{w}: handled_by {c} is not a DPC capability" for c, x in zip(ex.get("handled_by") or [], caps) if x is None]
        if caps and all(caps) and not any(ex.get("detector") in (x.get("discharges") or []) for x in caps):
            errs.append(f"{w}: no handling capability discharges the detector {ex.get('detector')}")
        if not ex.get("oracle"):
            errs.append(f"{w}: no oracle")
    stories = {e.get("story") for e in world.get("calendar") or []}
    declared = set(world.get("covers") or [])
    errs += [f"{name}: covers {s} but no incident has that story" for s in sorted(declared - stories)]
    errs += [f"{name}: required story {s} is not covered" for s in sorted((required_stories or set()) - stories)]
    errs += [f"{name}: product name '{p}'" for p in lint.products_in(yaml.safe_dump(world))]
    return errs


def load_domain(d):
    """All manifest files of one slice, by kind. Datasets are keyed source.dataset; others by name."""
    out = {"dataset": {}, "gold": {}, "metric": {}, "model": {}, "platform": None}
    for f in sorted((d / "manifest").rglob("*.yaml")):
        m = _y(f)
        k = m.get("kind", "dataset")
        if k == "dataset":
            out["dataset"][f"{m['source_name']}.{m['dataset_name']}"] = (f, m)
        elif k in ("gold_fact", "gold_dimension"):
            out["gold"][m["name"]] = (f, m)
        elif k == "metric_view":
            out["metric"][m["name"]] = (f, m)
        elif k == "ml_model":
            out["model"][m["name"]] = (f, m)
        elif k == "platform":
            out["platform"] = (f, m)
    return out


def lint_domain(d, cap_by_id, dac_ids, required_stories=None, root=ROOT):
    sdir = root / "dpm" / "schema"
    V = {k: _validator(sdir, f"{k}.schema.json") for k in ("gold", "metric", "ml_model", "platform")}
    dom = load_domain(d)
    rel = lambda f: str(f.relative_to(root))  # noqa: E731
    errs = []
    platform = None
    if dom["platform"]:
        f, platform = dom["platform"]
        errs += _schema_errors(V["platform"], platform, rel(f))
        errs += [f"{rel(f)}: product name '{p}'" for p in lint.products_in(f.read_text())]
    ds_cols = {}
    for key, (f, m) in dom["dataset"].items():
        c = _y(f.parent / m["contract"]) if "contract" in m else {}
        ds_cols[key] = contract_columns(c)
        errs += lint_dataset_v02(m, c, platform, rel(f)) if not [e for e in lint.lint_manifests_one(f, root)] else []
    gold_cols, dims, facts = {}, set(), set()
    for n, (f, g) in dom["gold"].items():
        (dims if g.get("kind") == "gold_dimension" else facts).add(n)
    for n, (f, g) in dom["gold"].items():
        e = _schema_errors(V["gold"], g, rel(f))
        if not e:
            c = _y(f.parent / g["contract"])
            gold_cols[n] = contract_columns(c)
            inputs = set().union(*[ds_cols.get(i["dataset"], set()) for i in g["inputs"]])
            e = lint_gold(g, c, ds_cols, dims, rel(f), inputs)
            if g["name"] != f.stem:
                e.append(f"{rel(f)}: name {g['name']} does not match the file name")
        errs += e
    for n, (f, mv) in dom["metric"].items():
        e = _schema_errors(V["metric"], mv, rel(f))
        errs += e or lint_metric(mv, facts, dims, rel(f))
    for n, (f, md) in dom["model"].items():
        e = _schema_errors(V["ml_model"], md, rel(f))
        errs += e or lint_model(md, gold_cols, rel(f))
    for kind in ("gold", "metric", "model"):
        for n, (f, _) in dom[kind].items():
            errs += [f"{rel(f)}: product name '{p}'" for p in lint.products_in(f.read_text())]
    if (d / "world.yaml").exists() and dom["platform"]:
        errs += lint_world(_y(d / "world.yaml"), set(dom["dataset"]), cap_by_id, dac_ids, rel(d / "world.yaml"),
                           required_stories)
    return errs


# ---------------------------------------------------------------- everything
def all_errors(root=ROOT):
    vocab, ports, caps = lint.load_vocab(root), lint.load_ports(root), lint.load_capabilities(root)
    dac_ids = {r["id"] for r in lint.load_obligations(root)}
    cap_by_id = {c["id"]: c for c in caps}
    port_names = {p["port"] for p in ports}
    adrs = load_adrs(root)
    readme = (root / "adr" / "README.md").read_text() if (root / "adr" / "README.md").exists() else None
    errs = lint_adrs(adrs, vocab, set(cap_by_id), dac_ids, readme)
    errs += lint_capability_adrs(caps, {a.get("id") for a in adrs})
    errs += [f"port {p['port']}: missing 'binds_in'" for p in ports if not p.get("binds_in")]
    errs += [f"port {p['port']}: binds_in may hold only engine and cloud" for p in ports
             if not set(p.get("binds_in") or []) <= {"engine", "cloud"}]
    cw = root / "crosswalks" / "deck.yaml"
    if cw.exists():
        errs += lint_crosswalk(_y(cw), vocab, set(cap_by_id), port_names)
    errs += lint_dbs(root, ports, dac_ids)
    for d in sorted((root / "slices").iterdir()):
        if (d / "manifest").is_dir() and any((d / "manifest").rglob("*.yaml")) and load_domain(d)["platform"]:
            errs += lint_domain(d, cap_by_id, dac_ids, STORIES, root)
    return errs


def summary(root=ROOT):
    stacks = load_stacks(root)
    return (f"ADRs: {len(load_adrs(root))}. DBS: {len(load_layers(root))} layers, {len(stacks)} stacks "
            f"({', '.join(stacks)}).")


if __name__ == "__main__":
    es = all_errors()
    for e in es:
        print("ERROR", e)
    print(summary())
    print(f"{len(es)} errors")
    sys.exit(1 if es else 0)
