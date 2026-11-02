# /// script
# requires-python = ">=3.9"
# dependencies = ["pyyaml"]
# ///
"""One-time authoring aid (step 8, 2 Nov 2026): write slice 1's DPC capabilities into dpc/capabilities/X*.yaml.

Slice 1 is "orders, source to silver": a shop's orders table replicated from its database (PA2) or dropped as
files (PA1), through landing and bronze to silver with history, surviving four planted incidents: the same batch
twice, a row deleted at the source, a late change, and a renamed column.

After this run the YAML files are the source and are edited by hand. Refuses to overwrite.

    uv run scripts/import_slice1.py
"""
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "dpc" / "capabilities"
ING = ["PA1", "PA2", "PA3", "PA4"]  # the archetypes that acquire data
ALL = [f"PA{i}" for i in range(1, 11)]


class NoAlias(yaml.SafeDumper):
    def ignore_aliases(self, data):
        return True


def dd(key, question, tension, resolution):
    return {"key": key, "question": question, "tension": tension, "resolution": resolution}


# (id, concern, level, core, stages, archetypes, port, policy, title, requirement, failure_mode, discharges, decisions)
CAPS = [
    ("DPC-0001", "X1", "MUST", True, ["platform"], ALL, "metadata_service", "own",
     "Every dataset is declared in a manifest",
     "Every source and dataset MUST be declared in a manifest file in version control, validated against a key "
     "registry before it is loaded; anything deployed without a manifest entry MUST be reported.",
     "A hand-made table fed the finance report for a year, and nobody knew it existed until its owner left.",
     ["CFG-01", "REL-01"],
     [dd("authoring_format", "Is the manifest authored as files or edited in the database?",
         "Files can be reviewed and replayed but need a loader; editing the database is quick and leaves no history.",
         "Files in version control are the only way in; a validating loader writes the database, and pipelines "
         "read only the database (agreed 27 Oct).")]),
    ("DPC-0002", "X1", "MUST", True, ["platform"], ALL, "metadata_service", "own",
     "One merged view of configuration per dataset",
     "Pipelines MUST read configuration only through one merged view per dataset (platform, then source, then "
     "dataset, the later one winning), never from code or from their own files.",
     "A connection string in a notebook pointed test at production for a week.",
     ["REL-04"],
     [dd("merge_order", "When the platform, the source and the dataset set the same key, which wins?",
         "A broad default is safe to set once; a narrow setting knows the data. Either can surprise someone.",
         "The narrowest wins (dataset over source over platform), and the merged view records where each value "
         "came from.")]),
    ("DPC-0003", "X1", "MUST", True, ["platform"], ALL, "metadata_service", "own",
     "Concerns on by default, off only by waiver",
     "Quality rules, reconciliation, lineage, freshness and cost tags MUST be on for every dataset unless a waiver "
     "with a reason, an approver and an expiry date turns one off; expired waivers MUST fail validation.",
     "A new table went live with no quality rules because the template made them optional.",
     ["CFG-02"], []),
    ("DPC-0004", "X2", "MUST", True, ["landing", "bronze", "silver"], ING, "orchestrator", "bind",
     "Jobs start on complete deliveries",
     "A load MUST start only when its delivery manifest exists, and a downstream job MUST start only when its "
     "inputs for the window are complete.",
     "A job started at two in the morning on a half-copied file and published half a day as a whole one.",
     ["ORCH-01"], []),
    ("DPC-0005", "X2", "MUST", False, ["platform"], ALL, "orchestrator", "bind",
     "Retries only for declared passing failures",
     "The retry policy MUST list which failures are passing (timeouts, throttling); every other failure MUST stop "
     "the run and alert without retrying.",
     "A data error was retried forty times overnight and the alert arrived after the morning report.",
     ["ORCH-02"], []),
    ("DPC-0006", "X2", "MUST", True, ["bronze", "silver"], ALL, "orchestrator", "own",
     "One writer per table at a time",
     "A table MUST have at most one run writing to it at a time; a second run MUST wait or fail with a clear "
     "message.",
     "A manual rerun overlapped the scheduled run and the day's totals were counted one and a half times.",
     ["ORCH-04"], []),
    ("DPC-0007", "X3", "MUST", True, ["bronze", "silver"], ING, "contract_enforcer", "adopt",
     "Every dataset has a contract file",
     "Every dataset MUST have a contract file that declares its columns, types, key and grain; the contract "
     "MUST use the open contract standard cited in core/standards.yaml rather than a format of our own.",
     "Nobody could say what one row of the orders table meant, so two teams counted orders two ways.",
     ["DES-04", "DQ-01"],
     [dd("contract_format", "Do we write our own contract format?",
         "Our own format fits exactly but nobody else reads it; the open standard is wider than we need.",
         "Adopt the open standard and reference it from the manifest; never copy schema into the manifest.")]),
    ("DPC-0008", "X3", "MUST", True, ["bronze", "silver"], ING, "contract_enforcer", "own",
     "Schema checked before silver",
     "Each batch MUST be compared with its contract before it reaches silver: a renamed, removed or retyped "
     "column MUST stop the load and name the column; a new column MUST be kept in bronze and reported, and MUST "
     "NOT reach silver until the contract adds it.",
     "A renamed column loaded as nulls for three weeks; the dashboard showed a slow fall that looked like a real "
     "business change.",
     ["SCH-01", "SCH-02"],
     [dd("additive_change", "Does a new source column stop the load?",
         "Stopping is safe but noisy, because sources add columns often; letting it through means silver changes "
         "shape without anyone agreeing.",
         "Keep it in bronze, report it, and let the contract owner add it. Bronze keeps everything; silver keeps "
         "only what was agreed.")]),
    ("DPC-0009", "X3", "MUST", True, ["platform"], ALL, None, "bind",
     "Contract and metric files are protected",
     "Contract and metric definition files MUST be protected paths that need review by their named owner; no "
     "pipeline or agent identity MAY merge a change to them.",
     "A job failed on a new null, so someone made the column nullable at night and the report showed blanks for "
     "a month.",
     ["GATE-02", "GATE-03"], []),
    ("DPC-0010", "X4", "MUST", True, ["silver"], ING, "quality_runner", "bind",
     "Quality rules run from the contract on every batch",
     "The quality rules in a dataset's contract MUST run on every batch, and each result MUST report rows "
     "examined and rows failed; a rule that examined zero rows MUST report error.",
     "The quality dashboard said zero failures for a week while the source sent nothing.",
     ["DQ-01", "GATE-01"], []),
    ("DPC-0011", "X4", "MUST", True, ["bronze", "silver"], ING, "quarantine", "own",
     "Failed rows quarantined with a reason",
     "A row that cannot be parsed or fails a blocking rule MUST go to quarantine with the rule id, the reason and "
     "the run id, the rest of the batch MUST continue, and quarantined rows MUST be replayable once fixed.",
     "One bad date in a million rows stopped the whole night's load.",
     ["DQ-02", "DQ-03"],
     [dd("stop_threshold", "When does quarantine become a stopped load?",
         "Quarantining everything keeps the load green while most of it is wrong; stopping on one bad row is fragile.",
         "Each dataset declares a share of quarantined rows above which the load stops; the default is low.")]),
    ("DPC-0012", "X4", "MUST", True, ["silver"], ING, "table_writer", "own",
     "Duplicate keys inside a delivery resolved by rule",
     "When rows in one delivery share a key, a declared rule (for example latest change sequence wins) MUST pick "
     "one, and every dropped row MUST be kept with the reason.",
     "The source sent two versions of the same order in one file and silver kept both.",
     ["DUP-03"], []),
    ("DPC-0013", "X4", "MUST", True, ["bronze"], ING, "quality_runner", "own",
     "Volume checked on every delivery",
     "Every delivery MUST be compared with its expected volume range, and an empty, missing or far-too-small "
     "delivery MUST alert and MUST NOT be marked a success.",
     "The source system went down and sent empty files for two days; every run was green.",
     ["DQ-04"], []),
    ("DPC-0014", "X4", "MUST", False, ["silver"], ING, None, "own",
     "Times in one declared zone",
     "The lander MUST convert every timestamp to the dataset's declared time zone, and the business date rule "
     "MUST be declared per dataset.",
     "Orders placed just before midnight landed on the next day and the daily totals never matched the till.",
     ["LATE-04"], []),
    ("DPC-0015", "X6", "MUST", True, ["sources", "bronze", "silver"], ING, "reconciler", "own",
     "Counts and totals compared at every hop",
     "Every run MUST record row counts and declared control totals at source, bronze and silver, compare each "
     "hop with the one before, and name the first hop where a difference appears.",
     "Silver was two percent short of the source and it took three days to find the filter that caused it.",
     ["REC-01", "REC-05"], []),
    ("DPC-0016", "X6", "MUST", True, ["platform"], ING, "reconciler", "own",
     "Tolerances and sign-off declared",
     "Every reconciliation MUST have a declared tolerance and a named person who signs off differences inside it.",
     "Every small difference became an incident until people stopped reading the alerts.",
     ["REC-03"], []),
    ("DPC-0017", "X6", "MUST", True, ["bronze", "silver"], ["PA1", "PA2"], "table_writer", "own",
     "Source deletes detected and applied by rule",
     "Rows deleted at the source MUST be detected, from the change feed where there is one and by comparing full "
     "key lists where there is not, and applied in silver by the dataset's declared delete rule (mark as deleted "
     "or remove).",
     "Cancelled orders were deleted at the source but stayed in the warehouse, and revenue was overstated for a "
     "quarter.",
     ["DEL-01"],
     [dd("delete_detection", "How are deletes found when the source has no change feed?",
         "Comparing full key lists finds every delete but costs a full read; trusting a delete flag is cheap but "
         "only works if the source sets it.",
         "Use the change feed when there is one; otherwise compare key lists on a declared schedule, and record "
         "which method a dataset uses.")]),
    ("DPC-0018", "X7", "MUST", True, ["bronze", "silver"], ALL, "lineage_emitter", "adopt",
     "Lineage emitted on every run",
     "Every run MUST emit a lineage event in the open lineage format naming what it read and wrote, and the "
     "recorded edges MUST be checked against the allowed one-way flow between layers.",
     "A source column was dropped and nobody could say which reports it fed.",
     ["LIN-01", "FLOW-01"], []),
    ("DPC-0019", "X8", "MUST", True, ["platform"], ALL, "telemetry", "bind",
     "Failures reach the dataset owner",
     "A failed or stopped run MUST alert the dataset's named owner or rota within the declared time, with the "
     "run id and the reason.",
     "The job failed on Friday night and the first person to know was a director on Monday.",
     ["OPS-01"], []),
    ("DPC-0020", "X9", "MUST", True, ["silver"], ING, "telemetry", "own",
     "Freshness measured per dataset",
     "Every dataset MUST record, on every run, the latest source change it contains, and compare its age with "
     "the declared freshness target.",
     "Every job was on time, but the source extract had stalled, so the data was two days old.",
     ["PERF-02"], []),
    ("DPC-0021", "X14", "MUST", True, ["platform"], ALL, "run_log", "own",
     "A run record with its configuration",
     "Every run MUST open a run record carrying a fingerprint and snapshot of its merged configuration, and close "
     "it with inputs, outputs, counts and status.",
     "A rerun of last month gave different numbers, and nobody could tell what the configuration had been.",
     ["CFG-03", "OPS-03"], []),
    ("DPC-0022", "X14", "MUST", True, ["bronze", "silver"], ING, "table_writer", "own",
     "Load metadata on every row",
     "Every bronze and silver row MUST carry the run id, the delivery id and the load time that wrote it.",
     "Finding which file produced one wrong row took a day of searching logs.",
     ["OPS-03"], []),
    ("DPC-0023", "X15", "MUST", True, ["landing"], ["PA1", "PA2", "PA3"], "landing_store", "own",
     "Deliveries kept as received, with a manifest",
     "Every delivery MUST land with a manifest (source, window, files, row count, checksum) and MUST NOT be "
     "changed afterwards, so a replay reads the same bytes.",
     "A replay of last Tuesday read a file that had since been overwritten, and gave different totals.",
     ["DUP-01", "DUP-02"], []),
    ("DPC-0024", "X15", "MUST", True, ["bronze", "silver"], ING, "table_writer", "own",
     "Every write carries a batch key",
     "Every write MUST carry the id of the delivery and window it came from, and writing a batch that was "
     "already written MUST change nothing.",
     "After an outage the source resent yesterday's file and revenue doubled on the dashboard.",
     ["DUP-01", "DUP-02", "ORCH-03"],
     [dd("batch_key_source", "Where does the batch key come from?",
         "A checksum of the file catches exact resends but not a resend with a new name; the source's own batch id "
         "catches renames but only if the source has one.",
         "Use the source's window plus a content checksum; record both in the run log.")]),
    ("DPC-0025", "X15", "MUST", True, ["silver"], ["PA1", "PA2"], "table_writer", "own",
     "History ordered by the source's change sequence",
     "Tables that keep history MUST order changes by the source's change sequence, not by arrival, and MUST end "
     "with one current row per key and no overlapping validity periods however often a batch is rerun.",
     "Two updates to one order arrived in the wrong order and the older status became current.",
     ["SCD-02"],
     [dd("ordering_column", "What orders the changes when the source gives no sequence?",
         "Arrival time is always there but wrong when deliveries overlap; a source timestamp can tie.",
         "Require a source sequence or timestamp in the contract; on a tie, use a declared tie-breaker column and "
         "record the tie.")]),
    ("DPC-0026", "X15", "MUST", True, ["silver"], ["PA1", "PA2"], "table_writer", "own",
     "Late changes corrected in place",
     "A change that arrives after later ones MUST be placed in history by its source sequence, and the validity "
     "periods around it MUST be corrected; the periods it affects MUST be marked for rebuild downstream.",
     "An address change arrived a week late and every order in between was shown at the old address.",
     ["LATE-01", "SCD-02"], []),
    ("DPC-0027", "X15", "MUST", True, ["platform"], ING, "metadata_service", "own",
     "Watermarks kept in the metadata store",
     "A dataset's watermark MUST be kept in the metadata store, never in the mover, and MUST advance in the same "
     "transaction that closes the run record.",
     "The copy tool was replaced and its saved position went with it, so a month was loaded twice.",
     ["HIST-03", "HIST-04"], []),
    ("DPC-0028", "X15", "MUST", True, ["bronze", "silver"], ING, "orchestrator", "own",
     "Any past window can be reloaded by parameter",
     "The normal job MUST accept a window as a parameter and reload it, changing only that window's rows and the "
     "rows derived from them.",
     "Reloading one bad day meant a hand-written script that also wiped the day after.",
     ["HIST-04"], []),
    ("DPC-0029", "X11", "MUST", True, ["platform"], ALL, "secret_store", "bind",
     "Credentials only from the secret store",
     "Jobs MUST get credentials from the secret store at run time; no credential MAY appear in code, "
     "configuration or the repository history.",
     "A database password in an old commit was found by a scanner a year after it was rotated, but the old one "
     "still worked on a forgotten replica.",
     ["REL-05"], []),
    ("DPC-0030", "X16", "MUST", True, ["platform"], ALL, None, "bind",
     "Everything that runs is in version control",
     "Code, manifests, contracts and schedules MUST be recreatable from version control alone, and the same "
     "build MUST be promoted between environments.",
     "A production job could not be rebuilt after an outage because its latest version existed only in the "
     "workspace.",
     ["REL-01", "REL-03"], []),
    ("DPC-0031", "X17", "MUST", True, ["platform"], ALL, None, "own",
     "Every claimed failure has a test that causes it",
     "Every incident kind the platform claims to handle MUST have a test that plants it on purpose and checks "
     "the expected detector fires.",
     "The late-data detector had never fired in two years; when it mattered, it was misconfigured.",
     ["TEST-05", "SIM-01"], []),
    ("DPC-0032", "X22", "MUST", True, ["platform"], ALL, "clock", "own",
     "Time only from the clock port",
     "Jobs MUST read the current time only from the clock port, so a simulation can move time and a replay can "
     "run as of a past day.",
     "A job that read the machine clock could not be replayed for last month; every replay used today's date.",
     ["SIM-01", "LATE-04"], []),
]


def main():
    if any(OUT.glob("*.yaml")):
        sys.exit("dpc/capabilities already has files; edit them instead.")
    names = yaml.safe_load((ROOT / "core" / "concerns.yaml").read_text())
    by = {}
    for (cid, concern, level, core, stages, arch, port, policy, title, req, fm, dis, decisions) in CAPS:
        rec = dict(id=cid, status="draft", since="0.1.0", level=level, title=title, concern=concern, stages=stages,
                   archetypes=arch, core=core, port=port, requirement=req, failure_mode=fm, discharges=dis)
        if decisions:
            rec["design_decisions"] = decisions
        rec.update(realization_policy=policy, slice=1, see_also=[])
        by.setdefault(concern, []).append(rec)
    OUT.mkdir(parents=True, exist_ok=True)
    for x in sorted(by, key=lambda s: int(s[1:])):
        head = f"# DPC capabilities for {x}, {names[x]['name']}. Normative: edit here.\n"
        (OUT / f"{x}.yaml").write_text(head + yaml.dump(by[x], Dumper=NoAlias, sort_keys=False, width=110))
    print(f"{len(CAPS)} capabilities in {len(by)} files")


if __name__ == "__main__":
    main()
