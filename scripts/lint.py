# /// script
# requires-python = ">=3.9"
# dependencies = ["pyyaml"]
# ///
"""Check DAC obligations follow dac/README.md. Exit 1 on any error.

    uv run scripts/lint.py
"""
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
    return {"concerns": y("core/concerns.yaml"), "stages": y("core/stages.yaml"), "standards": y("core/standards.yaml")}


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
            low = (r.get(k) or "").lower()
            for p in PRODUCTS:
                if re.search(rf"\b{re.escape(p)}\b", low):
                    errs.append(f"{w}: product name '{p}' in {k}")
    return errs


def lint_triage(recs, root=ROOT):
    """Every obligation imported from a review check is listed in triage.yaml, and nothing else is."""
    t = yaml.safe_load((root / "dac" / "triage.yaml").read_text())
    have = {r["review_check"] for r in recs if r.get("review_check")}
    want = set(t["obligation"])
    errs = [f"triage: {i} listed as obligation but no record has review_check {i}" for i in sorted(want - have)]
    errs += [f"triage: record with review_check {i} is not listed in triage.yaml" for i in sorted(have - want)]
    errs += [f"triage: {i} is both obligation and review_only" for i in sorted(want & set(t["review_only"]))]
    return errs


def main():
    recs = load_obligations()
    errs = lint(recs, load_vocab()) + lint_triage(recs)
    for e in errs:
        print("ERROR", e)
    core = sum(1 for r in recs if r.get("core"))
    print(f"{len(recs)} obligations ({core} core), {len(errs)} errors")
    sys.exit(1 if errs else 0)


if __name__ == "__main__":
    main()
