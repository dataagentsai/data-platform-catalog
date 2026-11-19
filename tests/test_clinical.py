"""Slice 3, the clinical trial: contracts, manifests and the world must agree with each other and with DAC and DPC,
and the world must cover every demo story. Table-driven: each row is one case with a name."""
import copy
import json
import sys
from pathlib import Path

import jsonschema
import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import lint  # noqa: E402
import lint_shape as ls  # noqa: E402

ROOT = lint.ROOT
D = ROOT / "slices" / "03-clinical"
DOM = ls.load_domain(D)
WORLD = yaml.safe_load((D / "world.yaml").read_text())
DAC = {r["id"] for r in lint.load_obligations()}
CAPS = {c["id"]: c for c in lint.load_capabilities()}
ODCS = json.loads((ROOT / "core" / "odcs-json-schema-v3.2.0.json").read_text())
CONTRACTS = sorted((D / "contracts").glob("*.odcs.yaml"))


def _entry(w, incident_id):
    return next(e for e in w["calendar"] if e["id"] == incident_id)


@pytest.mark.parametrize("path", CONTRACTS, ids=[p.name for p in CONTRACTS])
def test_contract_is_valid_odcs(path):
    v = jsonschema.validators.validator_for(ODCS)(ODCS)
    assert [e.message for e in v.iter_errors(yaml.safe_load(path.read_text()))] == []


def test_every_contract_is_used_by_exactly_one_manifest():
    used = [(f.parent / m["contract"]).resolve() for kind in ("dataset", "gold") for f, m in DOM[kind].values()]
    assert sorted(used) == sorted(p.resolve() for p in CONTRACTS)


def test_whole_domain_is_clean():
    assert ls.lint_domain(D, CAPS, DAC, ls.STORIES) == []


def test_base_dataset_rules_hold():
    assert [e for f, _ in DOM["dataset"].values() for e in lint.lint_manifests_one(f)] == []


SOURCES = {"edc": "database", "supply": "database", "lab": "file_drop", "site": "file_drop",
           "ctms_api": "rest_api", "coldchain_stream": "stream"}


@pytest.mark.parametrize("source,kind", sorted(SOURCES.items()))
def test_sources_are_in_the_world(source, kind):
    systems = [s for s in WORLD["systems"].values() if any(d.startswith(source + ".") for d in s["datasets"])]
    assert systems and systems[0]["kind"] == kind


@pytest.mark.parametrize("story", sorted(ls.STORIES))
def test_every_demo_story_has_an_incident(story):
    assert any(e.get("story") == story for e in WORLD["calendar"])


@pytest.mark.parametrize("fact", ["fact_visit_compliance", "fact_lab_out_of_range", "fact_enrolment",
                                  "fact_temperature_excursion"])
def test_facts_are_modelled_with_a_build(fact):
    g = DOM["gold"][fact][1]
    assert g["pipeline"] == "modelled" and g["build"]["kind"] in ("sql", "dataframe")


@pytest.mark.parametrize("metric", ["mv_visit_compliance", "mv_lab", "mv_enrolment", "mv_cold_chain"])
def test_each_metric_view_has_a_certified_measure(metric):
    assert any(m["certification"] == "certified" for m in DOM["metric"][metric][1]["measures"])


def test_every_ingest_mode_is_exercised():
    assert {m["ingest"]["mode"] for _, m in DOM["dataset"].values()} == {"push", "pull", "stream"}


def test_every_history_kind_is_exercised():
    assert {m["history"]["kind"] for _, m in DOM["dataset"].values()} == {"master", "transaction", "event", "snapshot"}


def test_the_treatment_arm_never_reaches_gold():
    gold_columns = {p["name"] for f, g in DOM["gold"].values()
                    for p in yaml.safe_load((f.parent / g["contract"]).read_text())["schema"][0]["properties"]}
    assert "treatment_arm" not in gold_columns


def test_every_subject_identifier_column_is_restricted():
    cols = [(f.name, p) for f in CONTRACTS for p in yaml.safe_load(f.read_text())["schema"][0]["properties"]
            if p["name"] == "subject_id"]
    assert cols and all(p.get("classification") == "restricted" for _, p in cols)


WORLD_CASES = [
    ("valid as written", lambda w: None, None),
    ("detector not in DAC", lambda w: w["calendar"][0]["expect"].update(detector="ZZZ-01"), "not a DAC obligation"),
    ("handler not in DPC", lambda w: w["calendar"][0]["expect"].update(handled_by=["DPC-9999"]), "not a DPC capability"),
    ("handlers do not discharge the detector", lambda w: w["calendar"][1]["expect"].update(handled_by=["DPC-0001"]),
     "no handling capability discharges"),
    ("incident after the clock ends", lambda w: w["calendar"][0].update(day=30), "outside the clock"),
    ("dataset no system delivers", lambda w: w["calendar"][0].update(dataset="edc.invoice"), "not delivered by any system"),
    ("unknown story", lambda w: w["calendar"][0].update(story="alien_invasion"), "unknown story"),
    ("no oracle", lambda w: w["calendar"][0]["expect"].pop("oracle"), "no oracle"),
    ("story dropped", lambda w: w.update(calendar=[e for e in w["calendar"] if e.get("story") != "mass_delete"]),
     "required story mass_delete is not covered"),
    ("system dataset without manifest", lambda w: w["systems"]["edc_db"]["datasets"].append("edc.invoice"),
     "edc.invoice has no manifest"),
    ("product name in the world", lambda w: w["systems"]["edc_db"].update(note="Oracle on Redshift"), "product name 'redshift'"),
    ("duplicate incident id", lambda w: w["calendar"].append(copy.deepcopy(w["calendar"][0])), "duplicate incident id"),
    ("no params block", lambda w: w["calendar"][0].pop("params"), "no params block"),
    ("params value is a list", lambda w: w["calendar"][0]["params"].update(shipments=[1, 2]), "must be a single value"),
    ("params day outside the clock", lambda w: _entry(w, "new-site-late")["params"].update(appears_day=20),
     "appears_day = 20 is not a day of the clock"),
    ("params share above 1", lambda w: _entry(w, "kit-copy-short")["params"].update(missing_share=40),
     "missing_share = 40 is not a share"),
    ("params until_day before the incident", lambda w: _entry(w, "lab-column-renamed")["params"].update(until_day=6),
     "until_day 6 is before the incident's day 8"),
    ("params from_day after the incident", lambda w: _entry(w, "subject-withdrawn")["params"].update(from_day=5),
     "from_day 5 is after the incident's day 4"),
]


@pytest.mark.parametrize("name,change,error", WORLD_CASES, ids=[c[0] for c in WORLD_CASES])
def test_world(name, change, error):
    w = copy.deepcopy(WORLD)
    change(w)
    errs = ls.lint_world(w, set(DOM["dataset"]), CAPS, DAC, "w", ls.STORIES)
    assert errs == [] if error is None else any(error in e for e in errs), errs


def test_no_product_names_in_the_slice():
    for f in sorted(D.rglob("*")):
        if f.is_file():
            assert lint.products_in(f.read_text()) == [], f.name


# The values the framework's world generator reads (world/domains/clinical.py) come from params: in the spec.
PARAMS_CASES = [
    ("lab-file-late", {"site": "busiest", "due_day": 4}),
    ("lab-column-renamed", {"site": "busiest", "column": "range_flag", "renamed_to": "flag", "until_day": 8}),
    ("enrolment-log-resent", {"site": "S-0002", "month": "2026-10"}),
    ("subject-withdrawn", {"from_day": 1}),
    ("adverse-event-out-of-order", {"from_day": 1}),
    ("kit-copy-short", {"missing_share": 0.40}),
    ("visits-planned-date-corrected", {"from_day": 1, "shift_days": 1, "activate_day": 11}),
    ("new-site-late", {"site": "S-0099", "country": "ZA", "appears_day": 13, "subjects": 2}),
    ("dispensing-feed-drops-rows", {}),
    ("site-status-changed", {"site": "S-0005", "from_status": "active", "to_status": "on_hold"}),
    ("temperature-readings-out-of-order", {"from_hour": 10, "hours": 2, "share": 0.30, "shipments": 6, "max_delay_s": 90}),
    ("temperature-stream-replayed", {"restart_hour": 14, "minutes": 45}),
]


@pytest.mark.parametrize("incident,params", PARAMS_CASES, ids=[c[0] for c in PARAMS_CASES])
def test_incident_params_match_the_world(incident, params):
    assert _entry(WORLD, incident)["params"] == params


def test_every_incident_has_a_params_case():
    assert sorted(e["id"] for e in WORLD["calendar"]) == sorted(c[0] for c in PARAMS_CASES)


def test_compressed_calendar_moves_every_incident_inside_days_2_and_3():
    moves = WORLD["calendars"]["compressed"]["moves"]
    assert sorted(moves) == sorted(e["id"] for e in WORLD["calendar"])
    assert {m["day"] for m in moves.values()} <= {2, 3}


ORDER_RULES = {  # key group: (what must hold between the incident's day and the key's day)
    ("from_day", "due_day"): ("a source day is before the incident", lambda day, v: v < day),
    ("activate_day", "appears_day"): ("an effect is after the incident", lambda day, v: v > day),
    ("until_day",): ("a lasting incident ends on or after its day", lambda day, v: v >= day),
}
_BY_ID = {e["id"]: e for e in WORLD["calendar"]}
CALENDAR_ORDER_CASES = [
    (f"{incident}.{key}: {rule}", move["day"], {**_BY_ID[incident].get("params", {}), **move}[key], holds)
    for incident, move in WORLD["calendars"]["compressed"]["moves"].items()
    for keys, (rule, holds) in ORDER_RULES.items()
    for key in keys
    if key in {**_BY_ID[incident].get("params", {}), **move}
]


@pytest.mark.parametrize("name,day,value,holds", CALENDAR_ORDER_CASES, ids=[c[0] for c in CALENDAR_ORDER_CASES])
def test_compressed_calendar_keeps_the_order_of_days(name, day, value, holds):
    assert holds(day, value)
