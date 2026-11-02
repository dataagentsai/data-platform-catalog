# /// script
# requires-python = ">=3.9"
# dependencies = ["pyyaml"]
# ///
"""One-time import (DE-021, 2 Nov 2026): turn data-project-review's Tech checks into DAC v0.1 obligations.

After this run, dac/obligations/*.yaml are the normative source and are edited by hand. This script is kept
so the triage is reproducible and reviewable; do not re-run it over edited files (it refuses if they exist).

    uv run scripts/import_dac_v0.py ~/data-project-review
"""
import sys
from pathlib import Path

import yaml


class NoAlias(yaml.SafeDumper):
    def ignore_aliases(self, data):
        return True


TITLES = {"DUP-02": "Rerunning a job leaves the result unchanged"}

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "dac" / "obligations"

# Short names for citations. DAMA chapters are from the 2nd edition (see core/standards.yaml: unverified).
DQ = {"standard": "DAMA-DMBOK", "ref": "Data Quality, chapter 13"}
MD = {"standard": "DAMA-DMBOK", "ref": "Metadata Management, chapter 12"}
SECU = {"standard": "DAMA-DMBOK", "ref": "Data Security, chapter 7"}
INTEG = {"standard": "DAMA-DMBOK", "ref": "Data Integration and Interoperability, chapter 8"}
OPSD = {"standard": "DAMA-DMBOK", "ref": "Data Storage and Operations, chapter 6"}
DWBI = {"standard": "DAMA-DMBOK", "ref": "Data Warehousing and Business Intelligence, chapter 11"}
GOV = {"standard": "DAMA-DMBOK", "ref": "Data Governance, chapter 3"}
MODEL = {"standard": "DAMA-DMBOK", "ref": "Data Modeling and Design, chapter 5"}


def odcs(ref):
    return {"standard": "ODCS", "ref": ref}


def iso(ref):
    return {"standard": "ISO-25012", "ref": ref}


ALL = ["bronze", "silver", "gold"]
# id: (concern, level, core, dimension, stages, statement, cites)
KEEP = {
    "DUP-01": ("X15", "MUST", True, "uniqueness", ["landing", "bronze", "silver", "gold"],
               "A file or batch delivered a second time MUST NOT change the row count or any key total in any layer.",
               [odcs("quality[].metric = duplicateValues"), DQ]),
    "DUP-02": ("X15", "MUST", True, "uniqueness", ALL,
               "Running the same job twice for the same window MUST leave every output table with the same fingerprint (row count, key totals) as running it once.",
               [DQ]),
    "DUP-03": ("X4", "MUST", True, "uniqueness", ["silver"],
               "Rows that share a declared key inside one source delivery MUST be resolved by a written rule, and every row the rule drops MUST be kept with the reason.",
               [odcs("quality[].metric = duplicateValues"), DQ]),
    "DUP-04": ("X15", "MUST", False, "uniqueness", ["bronze", "silver"],
               "Events replayed by a stream after a restart or rewind MUST NOT be counted twice in any output.",
               [DQ]),
    "DQ-01": ("X4", "MUST", True, None, ["silver", "gold"],
              "Every quality rule MUST be declared in the dataset's contract with a severity and a named owner; a rule that exists only in code does not count.",
              [odcs("quality[]"), DQ]),
    "DQ-02": ("X4", "MUST", True, "conformity", ["silver"],
              "A row that fails a blocking rule MUST be kept in quarantine with the rule id and the reason, and MUST be countable and replayable once fixed.",
              [odcs("quality[].severity"), DQ]),
    "DQ-03": ("X4", "MUST", False, "conformity", ["landing", "bronze"],
              "One malformed record MUST NOT stop the rest of its delivery from loading; the malformed record MUST be kept with the parse error.",
              [DQ]),
    "DQ-04": ("X9", "MUST", True, "completeness", ["bronze"],
              "A delivery that is empty, missing or far below its expected volume MUST raise an alert and MUST NOT be reported as a green success.",
              [odcs("quality[].metric = rowCount"), DQ]),
    "DEL-01": ("X6", "MUST", True, "completeness", ["bronze", "silver"],
               "Rows deleted at the source MUST be detected (from a change feed, a delete flag or a full-key comparison) and recorded in silver by the dataset's declared delete rule.",
               [INTEG]),
    "DEL-03": ("X6", "MUST", False, "consistency", ["gold", "semantic"],
               "A source delete MUST flow through every derived table, so that summaries still equal the sum of their detail after the delete.",
               [iso("consistency")]),
    "DES-04": ("X3", "MUST", True, "uniqueness", ["silver", "gold"],
               "Every table MUST declare its grain and its key, and the key MUST be tested for uniqueness on every run.",
               [odcs("schema[].properties[].primaryKey"), MODEL]),
    "HIST-03": ("X15", "MUST", False, "completeness", ["bronze", "silver"],
                "The switch from the first full load to incremental loads MUST lose no change made at the source while the full load was running.",
                [INTEG]),
    "HIST-04": ("X15", "MUST", True, None, ALL,
                "Reloading a past window MUST be a parameter of the normal job, and MUST change only that window's rows and the derived rows that depend on it.",
                [OPSD]),
    "SCD-02": ("X15", "MUST", True, "consistency", ["silver"],
               "A table that keeps history MUST end with exactly one current row per key and no overlapping validity periods, whatever order the changes arrive in and however often a batch is re-run.",
               [DWBI]),
    "SCD-04": ("X4", "SHOULD", False, "accuracy", ["gold"],
               "Facts SHOULD be joined to the version of a dimension that was valid at the fact's business date, unless the dataset declares otherwise.",
               [DWBI]),
    "LATE-01": ("X15", "MUST", True, "timeliness", ["silver", "gold"],
                "A late or corrected row MUST cause every period it affects to be rebuilt, within a declared look-back window, and nothing outside it.",
                [odcs("slaProperties[].property = latency")]),
    "LATE-02": ("X4", "MUST", False, "completeness", ["silver", "gold"],
                "A fact whose reference row has not yet arrived MUST be kept and linked once the reference arrives; it MUST NOT be dropped by an inner join.",
                [DWBI]),
    "LATE-03": ("X9", "SHOULD", False, "timeliness", ["bronze", "silver"],
                "A stream SHOULD declare how late an event may arrive and still be counted, and MUST count the events that arrive later than that.",
                [odcs("slaProperties[].property = latency")]),
    "LATE-04": ("X4", "MUST", False, "accuracy", ["silver"],
                "Every timestamp MUST carry or be converted to a declared time zone, and the business date rule MUST be declared per dataset.",
                [DQ]),
    "ORCH-01": ("X2", "MUST", True, "timeliness", ALL,
                "A job MUST start when its input data is complete, not at a clock time, and MUST NOT run on partial or stale input.",
                [OPSD]),
    "ORCH-02": ("X2", "MUST", False, None, ["platform"],
                "Only failures declared as passing (timeouts, throttling) MAY be retried automatically; a data error MUST fail at once and alert.",
                [OPSD]),
    "ORCH-03": ("X15", "MUST", True, None, ALL,
                "A job killed while writing and then restarted MUST produce the same output as a run that was never interrupted.",
                [OPSD]),
    "ORCH-04": ("X2", "MUST", False, None, ALL,
                "Two runs that write the same table at the same time MUST NOT both succeed with interleaved writes; the second MUST wait or fail clearly.",
                [OPSD]),
    "ORCH-05": ("X18", "MUST", False, None, ["platform"],
                "Every dataset MUST declare a recovery time and a data-loss limit, and a restore MUST have been timed against them.",
                [OPSD]),
    "ORCH-06": ("X18", "MUST", False, "completeness", ["bronze", "silver"],
                "A stream stopped for longer than a typical outage, or redeployed with changed code, MUST restart from where it stopped with no lost and no doubled events.",
                [OPSD]),
    "REC-01": ("X6", "MUST", True, "completeness", ["sources", "bronze", "silver", "gold"],
               "On every run, row counts and declared control totals MUST be compared at each hop from source to gold, and a difference MUST name the hop where it appeared.",
               [odcs("quality[].metric = rowCount"), DQ]),
    "REC-03": ("X6", "MUST", True, "accuracy", ["platform"],
               "Every reconciliation MUST have a declared tolerance and a named person who signs off differences inside it.",
               [DQ]),
    "SCH-01": ("X3", "MUST", False, "conformity", ["bronze", "silver"],
               "A new source column MUST be kept in bronze and reported, and MUST NOT reach silver or gold until the contract adds it.",
               [odcs("schema[]")]),
    "SCH-02": ("X3", "MUST", True, "conformity", ["bronze", "silver"],
               "A renamed, removed or retyped source column MUST stop the affected load with a message that names the column; it MUST NOT load as nulls.",
               [odcs("schema[].properties[]")]),
    "SEC-01": ("X12", "MUST", True, None, ["bronze", "silver", "gold"],
               "Every column MUST carry a classification, and personal data MUST be detected by scanning content, including free-text columns.",
               [odcs("schema[].properties[].classification"), SECU]),
    "SEC-02": ("X11", "MUST", True, None, ["silver", "gold", "semantic", "experiences"],
               "Access MUST be granted by role, and the lowest-privilege role MUST NOT be able to read a restricted column or row directly.",
               [SECU]),
    "SEC-03": ("X12", "MUST", True, None, ALL,
               "Every dataset holding personal data MUST declare a retention period, and an erasure request MUST remove the person from every table, version and extract within the declared time.",
               [odcs("slaProperties[].property = retention"), SECU]),
    "SEC-04": ("X14", "MUST", False, None, ["platform"],
               "Every read of restricted data MUST appear in an audit log that can be queried within an hour.",
               [SECU]),
    "ENV-01": ("X16", "MUST", True, None, ["platform"],
               "Development and test identities MUST NOT be able to write to production data.",
               [SECU]),
    "ENV-02": ("X11", "MUST", False, None, ["platform"],
               "Production jobs MUST run as service identities, and access MUST be granted to groups, never to named people.",
               [SECU]),
    "REL-01": ("X16", "MUST", True, None, ["platform"],
               "Everything that runs in production (code, configuration, contracts, schedules) MUST be recreatable from version control alone.",
               [OPSD]),
    "REL-02": ("X16", "MUST", False, None, ["platform"],
               "Changes to the main branch MUST go through review; direct pushes MUST be refused.",
               [GOV]),
    "REL-03": ("X16", "MUST", False, None, ["platform"],
               "The same build MUST be promoted from test to production by the pipeline, with no manual change in the target environment.",
               [OPSD]),
    "REL-04": ("X16", "MUST", False, None, ["platform"],
               "Environment-specific values MUST come from configuration, never from code.",
               [OPSD]),
    "REL-05": ("X11", "MUST", True, None, ["platform"],
               "No secret MUST ever be stored in the repository or its history.",
               [SECU]),
    "REL-06": ("X16", "SHOULD", False, None, ["platform"],
               "Infrastructure SHOULD be defined as code, so an environment can be rebuilt from the repository.",
               [OPSD]),
    "REL-07": ("X18", "MUST", False, None, ["platform"],
               "A release that changes a table MUST be reversible, including the data it changed, within a declared time.",
               [OPSD]),
    "OPS-01": ("X8", "MUST", True, None, ["platform"],
               "A failed run MUST reach a named person or rota who can act, within a declared time.",
               [OPSD]),
    "OPS-03": ("X14", "MUST", True, None, ALL,
               "Every run MUST leave a record (inputs, outputs, row counts, status, start and end), and every row MUST be traceable to the run and the delivery that wrote it.",
               [iso("traceability"), MD]),
    "PERF-02": ("X9", "MUST", True, "timeliness", ["gold", "semantic"],
                "Freshness MUST be measured end to end against the dataset's declared target on every run, and a miss MUST be reported.",
                [odcs("slaProperties[].property = timeOfAvailability"), iso("currentness")]),
    "PERF-05": ("X19", "SHOULD", False, None, ALL,
                "Table file counts and file sizes SHOULD be measured and kept inside declared bounds by routine maintenance.",
                [OPSD]),
    "COST-02": ("X10", "MUST", False, None, ["platform"],
                "Budgets, alerts and compute limits MUST stop one team, job or user from spending beyond a declared limit unnoticed.",
                [GOV]),
    "COST-03": ("X10", "MUST", True, None, ["platform"],
                "Every unit of spend MUST be attributable to a team and a job; untagged spend MUST be reported.",
                [GOV]),
    "COST-04": ("X10", "SHOULD", False, None, ["platform"],
                "Compute SHOULD NOT run when no work needs it; idle time per job SHOULD be measured.",
                [OPSD]),
    "SERV-01": ("X3", "MUST", True, None, ["gold", "semantic"],
                "Every consumer-facing dataset MUST have a published contract naming its fields, grain, freshness and owner.",
                [odcs("schema[]"), {"standard": "ODPS", "ref": "outputPorts[]"}]),
    "SERV-02": ("X9", "MUST", False, "timeliness", ["semantic", "experiences"],
                "A consumer MUST be able to see when the data was last complete, so stale data is never mistaken for current data.",
                [iso("currentness")]),
    "SERV-04": ("X13", "MUST", True, "consistency", ["semantic"],
                "Each business metric MUST be defined once, in one place, and every consumer MUST read that definition.",
                [{"standard": "Ossie", "ref": "metric"}, GOV]),
    "TEST-03": ("X17", "MUST", False, None, ["platform"],
                "Automated tests, including data tests, MUST run on every change and block the merge when they fail.",
                [DQ]),
    "TEST-05": ("X17", "MUST", True, None, ["platform"],
                "Every failure the design claims to handle MUST have a test that causes it on purpose.",
                [OPSD]),
}

# Checks that stay review-only: they are about a project's decisions or documents, not something a running
# platform can be tested for. They live on in data-project-review, unchanged.
REVIEW_ONLY = {
    "COST-01": "An estimate made before build, not a property of the running platform.",
    "DQ-05": "Profiling before design is a project step; the platform obligation is PROF-01.",
    "DEL-02": "Deciding what a delete means is a business call; DEL-01 holds the platform to the declared rule.",
    "DES-01": "A delivery practice (thin slice), not a platform property.",
    "DES-02": "Writing non-functional needs as numbers is a document check; the numbers then feed PERF-02 and ORCH-05.",
    "DES-05": "A design choice; DPC records the framework capability.",
    "DES-06": "A design choice made per consumer, not testable on the platform.",
    "ENV-03": "Network access in discovery is a project step.",
    "ENV-04": "Naming standards are a document check.",
    "ENV-05": "Fit with an existing platform is a review conversation.",
    "EST-01": "Estimation.", "EST-02": "Estimation.", "EST-03": "Estimation.", "EST-04": "Estimation.",
    "EST-05": "Estimation.", "EST-07": "Estimation.",
    "HAND-01": "Handover.", "HAND-02": "Handover.", "HAND-03": "Handover.", "HAND-06": "Handover.",
    "HIST-01": "History scope is a project decision; HIST-04 holds the platform to reload correctly.",
    "HIST-02": "Load on the source during extract is planned with the source owner.",
    "SCD-01": "Which tables keep history is a business call; SCD-02 holds the platform to it.",
    "SCD-03": "Asking source owners about key reuse is discovery work.",
    "OPS-05": "Hypercare is a plan item.",
    "PERF-01": "Volumes stated by source owners is discovery work.",
    "PERF-03": "Testing at production volume is a project step; the platform obligations are PERF-02 and PERF-05.",
    "PERF-04": "Skew analysis is a design step; DPC records the capability.",
    "REC-02": "Choosing the trusted business number is a business call; REC-01 does the comparing.",
    "REC-04": "A go-live checklist item.",
    "SCH-03": "Source teams warning before change is an agreement between people.",
    "SEC-05": "Where data may live is a compliance decision recorded in the binding.",
    "SERV-03": "Announcing change is a process; lineage (LIN-01) makes it possible.",
    "SERV-05": "Load testing consumer queries is a project step.",
    "TEST-01": "A test-strategy document check.", "TEST-02": "Test data realism is a project step.",
    "TEST-04": "User acceptance is a project step.",
}

# The delta (REUSE.md section 3 and PLAN.html rules R2-R9): platform rules no contract format covers.
NEW = [
    dict(id="GATE-01", title="Nothing passes by absence", concern="X4", level="MUST", core=True, dimension="completeness",
         stages=ALL + ["semantic"], rule="R7",
         statement="A check that examined zero rows, or did not run, MUST report error, never pass.",
         failure_mode="The quality dashboard said 0 failures for a week; the source had sent nothing, so nothing was checked.",
         test="Run every check against an empty input; each must report error.",
         evidence="Check results include the number of rows examined, and an error for each zero.",
         cites=[DQ], related=["DQ-04"]),
    dict(id="GATE-02", title="A contract is never loosened to make a job pass", concern="X3", level="MUST", core=True,
         dimension=None, stages=["platform"], rule="R6",
         statement="Contract and metric definition files MUST be protected paths: changing them MUST need review by their named owner, and no automated process MAY relax a rule to turn a failing run green.",
         failure_mode="A job failed on a new null column, so someone made the column nullable in the contract at night; the report then showed blanks for a month.",
         test="Open a change that relaxes one rule, as a pipeline identity and as an agent; both must be refused or held for the owner.",
         evidence="Branch protection or path ownership rules for contract and metric files; the refused attempt in the audit log.",
         cites=[odcs("quality[]"), GOV], related=["GATE-03", "SERV-04"]),
    dict(id="GATE-03", title="Agents propose, gates decide", concern="X21", level="MUST", core=True, dimension=None,
         stages=["platform"], rule="R6",
         statement="An agent MUST NOT change production directly; it MAY only propose a change to the manifest, and the same gates as a person's change MUST decide.",
         failure_mode="An assistant 'fixed' a failing job by editing the production table, and the fix was never in version control.",
         test="Give the agent a failing job; its only output must be a proposed change that runs through review and tests.",
         evidence="Agent identities hold no production write grants; every agent change is a reviewed merge.",
         cites=[GOV], related=["GATE-02", "HEAL-01"]),
    dict(id="FLOW-01", title="Data flows one way through the layers", concern="X7", level="MUST", core=True, dimension=None,
         stages=ALL + ["semantic", "experiences"], rule="R8",
         statement="Each layer MUST read only from the layer before it (gold from silver, semantic from gold, experiences from semantic); any other edge in the lineage MUST be reported.",
         failure_mode="A dashboard read silver directly to save a day; when gold's rules changed, two dashboards showed two revenues.",
         test="Compare the recorded lineage against the allowed edges; every other edge is a finding.",
         evidence="A lineage graph and the list of allowed edges it was checked against.",
         cites=[{"standard": "OpenLineage", "ref": "RunEvent"}, {"standard": "DAMA-DMBOK", "ref": "Data Architecture, chapter 4"}],
         related=["LIN-01"]),
    dict(id="SIM-01", title="Every incident kind has a planted test", concern="X22", level="MUST", core=True,
         dimension=None, stages=["platform"], rule="R9",
         statement="Every incident kind in the data world's calendar MUST be joined to the detector expected to fire, and each detector MUST have been seen to fire on a planted incident.",
         failure_mode="The late-data detector had never fired in two years; when it mattered, it was misconfigured.",
         test="Join the incident calendar to the detectors; every unmatched incident kind or never-fired detector is a gap.",
         evidence="The join table, with the run in which each detector last fired on a planted incident.",
         cites=[], related=["TEST-05"]),
    dict(id="CFG-01", title="Everything that runs was declared", concern="X1", level="MUST", core=True, dimension=None,
         stages=["platform"], rule="R2",
         statement="Every pipeline, table and check deployed MUST have a manifest entry that asked for it; the difference between what is deployed and what is declared MUST be reported.",
         failure_mode="A hand-made table fed the finance report for a year; nobody knew it existed until its owner left.",
         test="Diff the deployed inventory against the manifest; every undeclared object is a finding.",
         evidence="The inventory diff, empty or with each finding owned.",
         cites=[MD], related=["CFG-02", "CFG-03"]),
    dict(id="CFG-02", title="Cross-cutting concerns are on by default", concern="X1", level="MUST", core=True,
         dimension=None, stages=["platform"], rule="R5",
         statement="Quality rules, lineage, reconciliation, cost tags and freshness monitoring MUST be on for every dataset by default; turning one off MUST need a waiver with a reason, an approver and an expiry.",
         failure_mode="A new table went live with no quality rules because the template made them optional; it carried negative prices for a month.",
         test="Declare a dataset with no settings; every concern must be on. Remove one; the validator must demand a waiver.",
         evidence="The validator's rule, and the list of waivers with their expiry dates.",
         cites=[GOV], related=["CFG-01"]),
    dict(id="CFG-03", title="Every run records the configuration it ran under", concern="X14", level="MUST", core=True,
         dimension=None, stages=["platform"], rule=None,
         statement="Every run record MUST carry a fingerprint and a snapshot of the merged configuration it ran under, so a replay knows exactly what it is repeating.",
         failure_mode="A rerun of last month gave different numbers; the configuration had changed since, and nobody could tell what it had been.",
         test="Change one configuration value between two runs; the two run records must show different fingerprints and the old value must be readable.",
         evidence="Run log rows with a configuration fingerprint and snapshot.",
         cites=[MD], related=["OPS-03"]),
    dict(id="REC-05", title="Reconciliation names the hop that drifted", concern="X6", level="MUST", core=True,
         dimension="consistency", stages=["sources", "bronze", "silver", "gold"], rule=None,
         statement="When totals drift beyond tolerance, the result MUST name the first hop where the difference appeared, not only that source and report disagree.",
         failure_mode="Gold was 2% short of the source; it took three days to find the silver filter that caused it.",
         test="Plant a difference at one hop in test; the reconciliation result must name that hop.",
         evidence="Reconciliation results stored per hop per run.",
         cites=[DQ], related=["REC-01", "REC-03"]),
    dict(id="LIN-01", title="Every hop emits lineage", concern="X7", level="MUST", core=True, dimension=None,
         stages=ALL + ["semantic"], rule=None,
         statement="Every job MUST emit a lineage event naming what it read and what it wrote, on every run.",
         failure_mode="A source column was dropped, and nobody could say which reports it fed until users complained.",
         test="Run the chain once; every table must have a lineage edge back to its source.",
         evidence="Lineage events per run.",
         cites=[{"standard": "OpenLineage", "ref": "RunEvent"}, MD], related=["FLOW-01"]),
    dict(id="PROF-01", title="Every dataset is profiled and drift is visible", concern="X5", level="SHOULD", core=False,
         dimension=None, stages=["bronze", "silver"], rule=None,
         statement="Every dataset SHOULD be profiled on each run (counts, nulls, distinct values, ranges), and a change beyond a declared threshold SHOULD be reported.",
         failure_mode="A source started sending zero for unknown prices; nulls fell to nothing and nobody noticed the averages drop.",
         test="Change a column's distribution in a test delivery; the profile drift report must flag it.",
         evidence="Stored profiles per run and the drift report.",
         cites=[DQ, odcs("quality[].metric = nullValues")], related=["DQ-04"]),
    dict(id="HEAL-01", title="A self-healing fix goes through the same gates", concern="X20", level="MUST", core=False,
         dimension=None, stages=["platform"], rule="R6",
         statement="An automatic fix MUST be made in development, pass the same tests, be deployed through the normal pipeline, be verified after deployment, and roll back by itself if verification fails.",
         failure_mode="An automatic fix to a renamed column was applied straight to production and silently mapped the wrong field.",
         test="Trigger a known fixable incident; the fix must appear as a reviewed change, pass tests, and roll back when its check is made to fail.",
         evidence="The fix's change record, test run, deployment and verification result.",
         cites=[], related=["GATE-03"]),
]


def main(src):
    if any(OUT.glob("*.yaml")):
        sys.exit("dac/obligations already has files; this import runs once. Edit the files instead.")
    checks = {}
    for f in sorted((Path(src) / "packs" / "tech" / "checks").glob("*.yaml")):
        for c in yaml.safe_load(f.read_text()):
            checks[c["id"]] = c
    missing = set(checks) - set(KEEP) - set(REVIEW_ONLY)
    extra = (set(KEEP) | set(REVIEW_ONLY)) - set(checks)
    if missing or extra or set(KEEP) & set(REVIEW_ONLY):
        sys.exit(f"triage incomplete: missing={sorted(missing)} extra={sorted(extra)}")

    recs = []
    for cid, (concern, level, core, dim, stages, statement, cites) in KEEP.items():
        c = checks[cid]
        related = [r for r in c.get("related") or [] if r in KEEP]
        recs.append(dict(id=cid, status="draft", since="0.1.0", title=TITLES.get(cid, c["title"]), concern=concern, level=level,
                         core=core, dimension=dim, stages=stages, statement=statement,
                         failure_mode=" ".join(c["why"].split()), test=" ".join(c["fail_fast"].split()),
                         evidence=" ".join(c["evidence"]["looks_like"].split()), cites=cites,
                         review_check=cid, related=related))
    for n in NEW:
        n = dict(n)
        rule = n.pop("rule")
        rec = dict(id=n["id"], status="draft", since="0.1.0", **{k: v for k, v in n.items() if k != "id"})
        rec["review_check"] = None
        if rule:
            rec["plan_rule"] = rule
        recs.append(rec)

    by = {}
    for r in recs:
        by.setdefault(r["concern"], []).append(r)
    OUT.mkdir(parents=True, exist_ok=True)
    names = yaml.safe_load((ROOT / "core" / "concerns.yaml").read_text())
    for x in sorted(by, key=lambda s: int(s[1:])):
        head = f"# DAC obligations for {x}, {names[x]['name']}. Normative: edit here.\n"
        body = yaml.dump(sorted(by[x], key=lambda r: r["id"]), sort_keys=False, width=110, allow_unicode=True, Dumper=NoAlias)
        (OUT / f"{x}.yaml").write_text(head + body)
    (ROOT / "dac" / "triage.yaml").write_text(
        "# Which data-project-review Tech checks became DAC obligations (DE-021, 2 Nov 2026).\n"
        + yaml.safe_dump({"obligation": sorted(KEEP), "review_only": REVIEW_ONLY}, sort_keys=False, width=110))
    print(f"{len(KEEP)} kept, {len(REVIEW_ONLY)} review-only, {len(NEW)} new, {len(recs)} obligations in {len(by)} files")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else str(Path.home() / "data-project-review"))
