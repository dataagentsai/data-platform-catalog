# /// script
# requires-python = ">=3.9"
# dependencies = ["pyyaml", "jsonschema"]
# ///
"""Check the catalog: DAC obligations, archetypes, ports, capabilities and DPM manifests. Exit 1 on any error.

    uv run scripts/lint.py
"""
import json
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent

# Product and vendor names that must never appear in normative text (rule R1). They belong in bindings.
# Same list as data-project-review/scripts/lint.py, kept in step by hand.
PRODUCTS = ["databricks", "spark", "pyspark", "delta lake", "delta table", "unity catalog", "lakeflow", "auto loader",
            "autoloader", "dlt", "snowflake", "snowpipe", "bigquery", "redshift", "synapse", "fabric", "onelake",
            "power bi", "tableau", "looker", "adf", "data factory", "airflow", "dbt", "kafka", "kinesis", "event hub",
            "glue", "emr", "dataproc", "aws", "azure", "gcp", "google cloud", "s3", "adls", "iceberg", "hudi",
            "great expectations", "deequ", "soda", "terraform", "github", "gitlab", "jenkins", "jira", "confluence"]
TEXT_FIELDS = ["title", "statement", "failure_mode", "test", "evidence"]
REQUIRED = ["id", "status", "since", "title", "concern", "level", "core", "stages", "statement", "failure_mode",
            "test", "evidence"]
ID = re.compile(r"^[A-Z]{2,6}-\d{2}$")
LEVELS = {"MUST", "SHOULD", "MAY"}
STATUSES = {"draft", "active", "deprecated"}
DIMENSIONS = {"accuracy", "completeness", "conformity", "consistency", "coverage", "timeliness", "uniqueness"}  # ODCS 3.2.0


def load_vocab(root=ROOT):
    y = lambda p: yaml.safe_load((root / p).read_text())  # noqa: E731
    return {"concerns": y("core/concerns.yaml"), "stages": y("core/stages.yaml"), "standards": y("core/standards.yaml"),
            "archetypes": y("core/archetypes.yaml")}


def load_ports(root=ROOT):
    return yaml.safe_load((root / "dpc" / "ports.yaml").read_text()) or []


def load_capabilities(root=ROOT):
    recs = []
    for f in sorted((root / "dpc" / "capabilities").glob("*.yaml")):
        for r in yaml.safe_load(f.read_text()) or []:
            r["_file"] = f.stem
            recs.append(r)
    return recs


def products_in(text):
    low = (text or "").lower()
    return [p for p in PRODUCTS if re.search(rf"\b{re.escape(p)}\b", low)]


def load_obligations(root=ROOT):
    recs = []
    for f in sorted((root / "dac" / "obligations").glob("*.yaml")):
        for r in yaml.safe_load(f.read_text()) or []:
            r["_file"] = f.stem
            recs.append(r)
    return recs


def lint(recs, vocab):
    errs = []
    ids = [r.get("id") for r in recs]
    for r in recs:
        w = f"{r.get('_file', '?')}:{r.get('id', '?')}"
        for k in REQUIRED:
            if r.get(k) in (None, "", []):
                errs.append(f"{w}: missing '{k}'")
        for k in ("cites", "related"):
            if not isinstance(r.get(k), list):
                errs.append(f"{w}: '{k}' must be a list (empty is allowed)")
        if r.get("id") and not ID.match(r["id"]):
            errs.append(f"{w}: id must look like ABC-01")
        if ids.count(r.get("id")) > 1:
            errs.append(f"{w}: duplicate id")
        if r.get("status") and r["status"] not in STATUSES:
            errs.append(f"{w}: unknown status '{r['status']}'")
        if r.get("concern") and r["concern"] not in vocab["concerns"]:
            errs.append(f"{w}: unknown concern '{r['concern']}'")
        elif r.get("_file") and r.get("concern") and r["concern"] != r["_file"]:
            errs.append(f"{w}: concern {r['concern']} is in file {r['_file']}.yaml")
        lv = r.get("level")
        if lv and lv not in LEVELS:
            errs.append(f"{w}: level must be MUST, SHOULD or MAY")
        elif lv and lv not in (r.get("statement") or ""):
            errs.append(f"{w}: statement does not use its level word '{lv}'")
        if not isinstance(r.get("core"), bool):
            errs.append(f"{w}: core must be true or false")
        if r.get("dimension") is not None and r["dimension"] not in DIMENSIONS:
            errs.append(f"{w}: dimension '{r['dimension']}' is not an ODCS 3.2.0 dimension")
        for s in r.get("stages") or []:
            if s not in vocab["stages"]:
                errs.append(f"{w}: unknown stage '{s}'")
        for c in r.get("cites") or []:
            if not isinstance(c, dict) or c.get("standard") not in vocab["standards"]:
                errs.append(f"{w}: cite to unknown standard {c!r}")
            elif not c.get("ref"):
                errs.append(f"{w}: cite to {c['standard']} has no ref")
        for x in r.get("related") or []:
            if x not in ids:
                errs.append(f"{w}: related id '{x}' does not exist")
            if x == r.get("id"):
                errs.append(f"{w}: relates to itself")
        for k in TEXT_FIELDS:
            for p in products_in(r.get(k)):
                errs.append(f"{w}: product name '{p}' in {k}")
    return errs


def lint_archetypes(vocab):
    errs = []
    for k, a in vocab["archetypes"].items():
        if not re.match(r"^PA\d+$", k):
            errs.append(f"archetype {k}: id must look like PA1")
        for f in ("name", "arrives", "touches", "stages"):
            if not a.get(f):
                errs.append(f"archetype {k}: missing '{f}'")
        for st in a.get("stages") or []:
            if st not in vocab["stages"]:
                errs.append(f"archetype {k}: unknown stage '{st}'")
    return errs


PORT_REQUIRED = ["port", "status", "since", "service", "tier", "concerns", "stages", "summary", "kernel_owns",
                 "supplied_outside", "operations", "invariants"]


def lint_ports(ports, vocab, dac_ids):
    errs = []
    names = [p.get("port") for p in ports]
    for p in ports:
        w = f"port {p.get('port', '?')}"
        for k in PORT_REQUIRED:
            if p.get(k) in (None, "", []):
                errs.append(f"{w}: missing '{k}'")
        if p.get("port") and not re.match(r"^[a-z][a-z_]*$", p["port"]):
            errs.append(f"{w}: name must be lower_snake_case")
        if names.count(p.get("port")) > 1:
            errs.append(f"{w}: duplicate port")
        if p.get("service") and p["service"] not in ("A", "B", "C", "platform"):
            errs.append(f"{w}: service must be A, B, C or platform")
        if p.get("tier") and p["tier"] not in ("core", "later"):
            errs.append(f"{w}: tier must be core or later")
        for c in p.get("concerns") or []:
            if c not in vocab["concerns"]:
                errs.append(f"{w}: unknown concern '{c}'")
        for st in p.get("stages") or []:
            if st not in vocab["stages"]:
                errs.append(f"{w}: unknown stage '{st}'")
        texts = [p.get("summary"), p.get("kernel_owns"), p.get("supplied_outside")]
        for op in p.get("operations") or []:
            if not op.get("name") or not op.get("intent"):
                errs.append(f"{w}: operation needs a name and an intent")
            texts.append(op.get("intent"))
        for inv in p.get("invariants") or []:
            for k in ("must", "because", "obligation", "checkable"):
                if not inv.get(k):
                    errs.append(f"{w}: invariant missing '{k}'")
            if inv.get("obligation") and inv["obligation"] not in dac_ids:
                errs.append(f"{w}: invariant obligation '{inv['obligation']}' is not a DAC id")
            if inv.get("checkable") and inv["checkable"] not in ("static", "dynamic"):
                errs.append(f"{w}: checkable must be static or dynamic")
            texts += [inv.get("must"), inv.get("because")]
        for t in texts:
            for prod in products_in(t):
                errs.append(f"{w}: product name '{prod}'")
    return errs


CAP_REQUIRED = ["id", "status", "since", "level", "title", "concern", "stages", "archetypes", "core", "requirement",
                "failure_mode", "discharges", "realization_policy"]


def lint_capabilities(caps, vocab, dac_ids, port_names):
    errs = []
    ids = [c.get("id") for c in caps]
    for c in caps:
        w = f"{c.get('_file', '?')}:{c.get('id', '?')}"
        for k in CAP_REQUIRED:
            if c.get(k) in (None, "", []):
                errs.append(f"{w}: missing '{k}'")
        if c.get("id") and not re.match(r"^DPC-\d{4}$", c["id"]):
            errs.append(f"{w}: id must look like DPC-0001")
        if ids.count(c.get("id")) > 1:
            errs.append(f"{w}: duplicate id")
        if c.get("status") and c["status"] not in STATUSES:
            errs.append(f"{w}: unknown status '{c['status']}'")
        if c.get("concern") and c["concern"] not in vocab["concerns"]:
            errs.append(f"{w}: unknown concern '{c['concern']}'")
        lv = c.get("level")
        if lv and lv not in LEVELS:
            errs.append(f"{w}: level must be MUST, SHOULD or MAY")
        elif lv and lv not in (c.get("requirement") or ""):
            errs.append(f"{w}: requirement does not use its level word '{lv}'")
        if not isinstance(c.get("core"), bool):
            errs.append(f"{w}: core must be true or false")
        for st in c.get("stages") or []:
            if st not in vocab["stages"]:
                errs.append(f"{w}: unknown stage '{st}'")
        for a in c.get("archetypes") or []:
            if a not in vocab["archetypes"]:
                errs.append(f"{w}: unknown archetype '{a}'")
        if c.get("port") is not None and c.get("port") not in port_names:
            errs.append(f"{w}: unknown port '{c.get('port')}'")
        for d in c.get("discharges") or []:
            if d not in dac_ids:
                errs.append(f"{w}: discharges '{d}', which is not a DAC id")
        if c.get("realization_policy") and c["realization_policy"] not in ("own", "adopt", "bind"):
            errs.append(f"{w}: realization_policy must be own, adopt or bind")
        for dd in c.get("design_decisions") or []:
            for k in ("key", "question", "tension", "resolution"):
                if not dd.get(k):
                    errs.append(f"{w}: design decision missing '{k}'")
        for x in c.get("see_also") or []:
            if x not in ids:
                errs.append(f"{w}: see_also id '{x}' does not exist")
        texts = [c.get("title"), c.get("requirement"), c.get("failure_mode")]
        texts += [dd.get(k) for dd in c.get("design_decisions") or [] for k in ("question", "tension", "resolution")]
        for t in texts:
            for prod in products_in(t):
                errs.append(f"{w}: product name '{prod}'")
    return errs


def uncovered(obligations, caps):
    """DAC ids no capability discharges. Reported now; an error from the v0.1 gate (DE-027)."""
    done = {d for c in caps for d in c.get("discharges") or []}
    return sorted(r["id"] for r in obligations if r["id"] not in done)


def lint_triage(recs, root=ROOT):
    """Every obligation imported from a review check is listed in triage.yaml, and nothing else is."""
    t = yaml.safe_load((root / "dac" / "triage.yaml").read_text())
    have = {r["review_check"] for r in recs if r.get("review_check")}
    want = set(t["obligation"])
    errs = [f"triage: {i} listed as obligation but no record has review_check {i}" for i in sorted(want - have)]
    errs += [f"triage: record with review_check {i} is not listed in triage.yaml" for i in sorted(have - want)]
    errs += [f"triage: {i} is both obligation and review_only" for i in sorted(want & set(t["review_only"]))]
    return errs


def lint_manifest(manifest, contract, keys, schema, archetype_ids, name="manifest"):
    """DPM (DE-022): the JSON schema, then the cross-file rules a schema cannot express."""
    from jsonschema import Draft202012Validator
    errs = [f"{name}: {'/'.join(map(str, e.path)) or '(top)'}: {e.message}"
            for e in sorted(Draft202012Validator(schema).iter_errors(manifest), key=lambda e: list(e.path))]
    if errs:
        return errs
    allowed = set(keys["dataset_config"]) | {p["key"] for p in keys["proposed"]}
    errs += [f"{name}: config key '{k}' is not in dpm/keys.yaml" for k in manifest["config"] if k not in allowed]
    if str(manifest["contract_version"]) != str(contract.get("version")):
        errs.append(f"{name}: pins contract {manifest['contract_version']} but the contract is {contract.get('version')}")
    cols = {p["name"] for s in contract.get("schema", []) for p in s.get("properties", [])}
    used = [("load.history_order_by", manifest["load"].get("history_order_by")),
            ("dedup.order_by", (manifest.get("dedup") or {}).get("order_by"))]
    used += [("dedup.business_keys", k) for k in (manifest.get("dedup") or {}).get("business_keys", [])]
    used += [(f"reconciliation measure {m['name']}", m.get("column")) for m in manifest["reconciliation"]["measures"]]
    errs += [f"{name}: {where} uses '{c}', which is not a contract column" for where, c in used if c and c not in cols]
    errs += [f"{name}: archetype {a} is not in core/archetypes.yaml" for a in manifest["archetypes"]
             if a not in archetype_ids]
    band = (manifest.get("volume") or {}).get("expected_rows_per_delivery")
    if band and band["min"] > band["max"]:
        errs.append(f"{name}: volume band min {band['min']} is above max {band['max']}")
    return errs


def lint_manifests(root=ROOT):
    keys = yaml.safe_load((root / "dpm" / "keys.yaml").read_text())
    schema = json.loads((root / "dpm" / "schema" / "dataset.schema.json").read_text())
    arch = set(yaml.safe_load((root / "core" / "archetypes.yaml").read_text()))
    errs = []
    for m_path in sorted(root.glob("slices/*/manifest/*.yaml")):
        m = yaml.safe_load(m_path.read_text())
        c = yaml.safe_load((m_path.parent / m["contract"]).read_text()) if "contract" in m else {}
        errs += lint_manifest(m, c, keys, schema, arch, str(m_path.relative_to(root)))
    return errs


def lint_binding(binding, schema, port_names, dac_ids, name="binding"):
    """DBS (DE-023): the schema, then every port and obligation it names must exist."""
    from jsonschema import Draft202012Validator
    errs = [f"{name}: {'/'.join(map(str, e.path)) or '(top)'}: {e.message}"
            for e in sorted(Draft202012Validator(schema).iter_errors(binding), key=lambda e: list(e.path))]
    if errs:
        return errs
    errs += [f"{name}: binds '{p}', which is not a port in dpc/ports.yaml" for p in binding["bindings"]
             if p not in port_names]
    ids = [(p, i) for p, b in binding["bindings"].items() for i in b["proves"]]
    ids += [("accepted_gaps", g["obligation"]) for g in binding["accepted_gaps"]]
    errs += [f"{name}: {where} names {i}, which is not a DAC obligation" for where, i in ids if i not in dac_ids]
    return errs


def coverage_by_concern(binding, ports):
    """Per concern: the ports bound, their coverage, and who fills each gap. Generated, never hand-written."""
    out = {}
    for p in ports:
        b = binding["bindings"].get(p["port"])
        for c in p.get("concerns") or []:
            out.setdefault(c, []).append((p["port"], b["coverage"] if b else "unbound",
                                          (b.get("gap_filled_by") or {}).get("approach", "") if b else ""))
    return out


def lint_bindings(root=ROOT, ports=None, dac_ids=None):
    schema = json.loads((root / "dbs" / "schema" / "binding.schema.json").read_text())
    ports = ports if ports is not None else load_ports(root)
    dac_ids = dac_ids if dac_ids is not None else {r["id"] for r in load_obligations(root)}
    errs = []
    for f in sorted(root.glob("slices/*/binding-*.yaml")):
        errs += lint_binding(yaml.safe_load(f.read_text()), schema, {p["port"] for p in ports}, dac_ids,
                             str(f.relative_to(root)))
    return errs


def main():
    recs, vocab = load_obligations(), load_vocab()
    ports, caps = load_ports(), load_capabilities()
    dac_ids = {r["id"] for r in recs}
    errs = (lint(recs, vocab) + lint_triage(recs) + lint_archetypes(vocab)
            + lint_ports(ports, vocab, dac_ids) + lint_capabilities(caps, vocab, dac_ids, {p["port"] for p in ports})
            + lint_manifests() + lint_bindings(ports=ports, dac_ids=dac_ids))
    for e in errs:
        print("ERROR", e)
    core = sum(1 for r in recs if r.get("core"))
    gap = uncovered(recs, caps)
    print(f"DAC: {len(recs)} obligations ({core} core). DPC: {len(ports)} ports, {len(caps)} capabilities.")
    print(f"Coverage: {len(recs) - len(gap)} of {len(recs)} obligations discharged by a capability.")
    print(f"{len(errs)} errors")
    sys.exit(1 if errs else 0)


if __name__ == "__main__":
    main()
