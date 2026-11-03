# /// script
# requires-python = ">=3.9"
# dependencies = ["pyyaml"]
# ///
"""One-time import (DE G1, 4 Nov 2026): the 134 cards of ~/Engineering-Best-Practices.html into practices/.

Kept for provenance, like import_dac_v0.py. Do not run it again: practices/*.yaml are now the source, edited by
hand, and the page is generated from them by build_practices_page.py.

    git -C ~/apollo-deck show cbf5283:site/Engineering-Best-Practices.html > /tmp/original.html
    uv run scripts/import_practices.py /tmp/original.html

The input must be the original hand-written page (apollo-deck commit cbf5283), not the generated one.
"""
import json
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "practices"

KIND = {"P": "principle", "B": "practice", "A": "anti-pattern"}
LAYER = {"L": "landing", "B": "bronze", "S": "silver", "G": "gold", "M": "semantic", "X": "platform"}

# Card number on the page (1-based) -> (DAC ids it serves, placeholder ADR ids from session B's list).
# ADR placeholders, in the order session B's brief lists them:
#   001 silver source-aligned, 002 pull straight to bronze, 003 two gold pipeline kinds, 004 hash surrogate keys,
#   005 SCD2 as-of joins, 006 facts as tables by window recompute, 007 the 13 bronze-to-silver stages,
#   008 column projection all by default, 009 DQ severity sets the action, 010 metadata store behind stored
#   procedures, 011 liquid clustering and automatic upkeep, 012 catalog per environment and layer,
#   013 IO only at the edges, 014 two-layer binding, 015 kernel, ports, adapters and realms.
MAP = {
    1: (["CFG-01", "ENG-01", "CFG-05"], ["ADR-010"]), 2: (["REL-01", "CFG-01"], ["ADR-010"]),
    3: (["GATE-03", "HEAL-01"], ["ADR-023"]), 4: (["ENG-01"], ["ADR-003", "ADR-007"]),
    5: (["PURE-01", "TEST-03"], ["ADR-013"]), 6: (["IDEMP-01", "DUP-01", "DUP-02"], []),
    7: (["TEST-03", "GATE-01", "SCH-02", "REL-02"], []), 10: (["FLOW-01", "RAW-01"], ["ADR-001"]),
    11: (["OPS-03", "CFG-02", "GATE-01"], []), 12: (["PII-01", "SEC-01", "SEC-02", "REL-05"], []), 13: (["CFG-02", "COST-03"], []),
    14: (["DES-04", "SERV-01"], []),
    15: (["CFG-04"], ["ADR-010"]), 16: (["CFG-04", "OPS-03", "REL-01"], ["ADR-010"]), 17: (["CFG-05"], ["ADR-010"]),
    18: (["CFG-03", "CFG-05"], ["ADR-010"]), 19: (["DES-04", "DUP-03"], []), 20: (["CAT-01", "SEC-01"], []),
    21: (["SERV-01", "SCH-01", "SCH-02", "ING-01"], []), 22: (["REL-04", "CFG-05"], []),
    23: (["ENV-01"], ["ADR-012"]), 24: (["NAME-01"], ["ADR-012"]), 25: (["LIN-01", "OPS-03"], []),
    26: (["SERV-01", "SERV-04"], []), 27: (["SEC-04"], []), 28: (["ENV-01", "REL-03", "ENV-02"], []),
    29: (["PII-01"], []), 30: (["SEC-02", "SEC-01"], []), 31: (["SEC-02"], []), 32: (["SEC-03"], []),
    33: (["SEC-01"], []), 34: (["ENC-01"], ["ADR-012"]), 35: (["PII-01"], []),
    36: (["ENG-01", "ING-01"], []), 37: (["ING-01"], ["ADR-002"]), 38: (["DUP-01", "FILE-01", "DQ-04"], []),
    39: (["ING-01", "TEST-05"], ["ADR-002"]), 40: (["DQ-04", "DEL-01"], []), 41: (["HIST-03", "HIST-04"], []),
    42: (["ING-01", "PII-01"], []), 43: (["ENC-01", "ING-01"], []), 44: (["LATE-03", "DUP-04", "ORCH-06"], []),
    45: (["DUP-01", "RAW-01"], []), 46: (["ING-01", "FLOW-01"], []),
    47: (["CFG-01"], []), 48: (["ORCH-01", "COST-04"], []), 49: (["ORCH-04"], []), 50: (["DQ-03", "OPS-01"], []),
    51: (["FILE-01"], []), 52: (["ORCH-01"], []), 53: (["ORCH-01"], []),
    54: (["RAW-01", "DUP-01"], []), 55: (["RAW-01", "SCH-01"], []), 56: (["RAW-01"], []),
    57: (["ENG-01"], ["ADR-007"]), 58: (["PURE-01", "TEST-03"], ["ADR-007", "ADR-013"]), 59: (["DUP-02", "COST-04"], []),
    60: (["CFG-01", "ENG-01"], []), 61: (["SCH-01", "SCH-02"], ["ADR-007"]),
    62: (["PROJ-01"], ["ADR-007", "ADR-008"]), 63: (["DQ-01", "PROF-01"], ["ADR-007"]),
    64: (["SCH-02", "DQ-02"], ["ADR-007"]), 65: (["LATE-04"], ["ADR-007"]), 66: (["PII-01"], ["ADR-007"]),
    67: (["REC-01"], ["ADR-007"]), 68: (["DQ-01", "DQ-02", "SEV-01", "QUAR-01"], ["ADR-007", "ADR-009"]),
    69: (["DUP-03", "DES-04"], ["ADR-007"]), 70: (["SCD-02", "DEL-01", "DEL-03"], ["ADR-007", "ADR-016"]),
    71: (["OPS-03", "LIN-01"], ["ADR-007"]), 72: (["ENG-01"], ["ADR-007"]),
    73: (["DQ-02", "REC-01", "QUAR-01"], []), 74: (["FLOW-01"], ["ADR-001"]),
    75: (["ENG-01"], ["ADR-003"]), 76: (["PURE-01", "TEST-03"], ["ADR-003", "ADR-013"]),
    77: (["LATE-02", "PUB-01"], ["ADR-004"]), 78: (["LATE-01", "DUP-02"], ["ADR-006"]), 79: (["KEY-01"], ["ADR-004"]),
    80: (["SCD-04"], ["ADR-005"]), 81: (["SERV-04", "DES-04"], []), 82: (["DES-04"], []),
    83: (["PUB-01", "COST-02"], ["ADR-006"]), 84: (["GOLD-01", "DUP-02"], ["ADR-006"]), 85: (["PUB-01", "REC-01"], []),
    86: (["SERV-02", "LATE-01"], ["ADR-018"]), 87: (["HIST-04", "LATE-01"], ["ADR-017"]), 88: (["LATE-02"], ["ADR-004"]),
    89: (["LATE-01"], ["ADR-006"]), 90: (["GOLD-01"], ["ADR-006"]), 91: (["KEY-01"], ["ADR-004"]),
    92: (["SCD-04"], ["ADR-005"]), 93: (["DES-04"], []), 94: (["SERV-04"], []),
    95: (["PURE-01", "TEST-03"], ["ADR-013"]), 96: (["ENG-01"], ["ADR-003", "ADR-007"]),
    97: (["PUB-01", "COST-02"], ["ADR-006"]), 98: (["ORCH-01", "SERV-02"], ["ADR-018"]), 99: (["PUB-01"], []),
    100: (["ENV-02", "HIST-04"], ["ADR-017"]), 101: (["LATE-02", "OPS-03"], ["ADR-004"]), 102: (["DES-04"], []),
    103: (["SERV-04", "REL-01"], []), 104: (["SERV-04"], []), 105: (["SERV-04", "SERV-01", "GATE-02"], ["ADR-022"]),
    106: (["SERV-04", "FLOW-01"], ["ADR-022"]), 107: (["FLOW-01", "SERV-04"], ["ADR-022"]),
    108: (["CFG-02", "DQ-01", "REC-01"], []), 109: (["DQ-01", "CFG-05"], []), 110: (["SEV-01", "DQ-02"], ["ADR-009"]),
    111: (["PROF-01"], []), 112: (["REC-01", "REC-03", "REC-05"], []),
    113: (["REL-02", "REL-05"], []), 114: (["TEST-03", "REL-02"], []), 115: (["TEST-03"], []),
    116: (["TEST-03", "TEST-05"], []), 117: (["SIM-01", "TEST-05"], []), 118: (["REL-03", "TEST-03"], []),
    119: (["TEST-03", "PURE-01"], []),
    120: (["REL-06"], []), 121: (["CFG-01", "REL-01"], []), 122: (["REL-02", "REL-03", "TEST-03"], []), 123: (["CFG-01", "REL-01"], []),
    124: (["OPS-03"], []), 125: (["OPS-03", "COST-03"], []), 126: (["PERF-02", "SERV-02"], []), 127: (["OPS-01"], []),
    128: (["OPS-01", "ORCH-03"], []),
    129: (["COST-03"], []), 130: (["COST-02"], []), 131: (["COST-04", "COST-02"], []), 132: (["COST-04", "COST-02"], []),
    133: (["PERF-05"], ["ADR-011"]), 134: (["PERF-05"], ["ADR-011"]),
}

DROPPED = {
    8: "An architecture rule, not something a running platform can be tested for. It is owned by ADR-015 (kernel, "
       "ports, adapters and realms), ADR-020 (every adapter passes its port's contract test) and the DPC ports in "
       "dpc/ports.yaml.",
    9: "A design-review habit (reuse first, build only the gap), not a property of the platform. It belongs in the "
       "ADRs' 'options considered' sections and in the charter, not in DAC.",
}

# Rule R1: title, why and instead are normative and carry no product names. Product names stay in `how`
# (and in the enforcement notes), which are binding examples for the AWS and Databricks binding.
REWRITE = {
    20: {"title": "Sync descriptions, tags and keys to the data catalog",
         "why": "Conversational query tools, tag-based access policies and catalog search are only as good as the "
                "descriptions and tags on the tables."},
    27: {"title": "Audit from the platform's own access logs and the cloud's logs"},
    33: {"title": "A content scanner checks landing for personal data"},
    34: {"title": "Own storage and encryption key per catalog; private network"},
    42: {"title": "Managed connectors only for SaaS without personal data",
         "why": "The platform's managed connectors are quick, but they bypass our lander's tokenising, file log and "
                "contract checks."},
    47: {"title": "One job per source"},
    55: {"title": "Keep JSON whole in a semi-structured column"},
    94: {"instead": "Put calculations in gold build() or in the semantic layer's metric definitions."},
    97: {"instead": "Use a table written by the window recompute job."},
    102: {"instead": "Build a star schema; add a wide view or a semantic-layer view on top when a use case needs it."},
    103: {"title": "Metric definitions in YAML, deployed to the catalog"},
    106: {"title": "One layer serves dashboards, conversational query, agents and APIs"},
    107: {"title": "Pointing a conversational query tool at raw silver tables",
          "why": "The tool then guesses joins and meanings and gives plausible but wrong answers.",
          "instead": "Point it at metric definitions and described gold tables."},
    111: {"title": "Profiling and drift monitoring"},
    114: {"why": "Many engine and platform mistakes can be found without running anything."},
    116: {"title": "Integration tests on a local engine and table format"},
    117: {"title": "Simulation scenarios in a data twin"},
    119: {"instead": "Write table-driven unit tests first, then integration tests on a local engine."},
    120: {"title": "Infrastructure as code for the cloud and the data platform"},
    121: {"title": "Deployment bundles generated from metadata"},
    122: {"title": "CI promotes every change through the environments"},
    127: {"title": "Alerts routed to on-call"},
    131: {"title": "A waste and anomaly finder reads the bills"},
    132: {"title": "Serverless and the fast engine by default"},
    133: {"title": "Automatic clustering and automatic table upkeep"},
    134: {"instead": "Use automatic clustering and leave upkeep to the platform's automatic optimization."},
}

# Proposed checks the bundle does not have yet -> the DAC obligations each would enforce.
PROPOSED_DAC = {
    "SL-CLEAN-33": ["REL-04", "ING-01"], "SL-COST-CODE-26": ["PERF-05"], "SL-GOLD-01": ["GOLD-01"],
    "SL-GOLD-02": ["KEY-01"], "SL-GOLD-03": ["LATE-02"], "SL-GOLD-04": ["PUB-01", "COST-02"],
    "SL-GOLD-05": ["SERV-04"], "SL-JOB-01": ["ORCH-04"], "SL-JOB-02": ["ORCH-01"], "SL-LAYER-01": ["FLOW-01"],
    "SL-LAYER-02": ["ENG-01"], "SL-META-01": ["DES-04", "SEC-01", "CFG-02", "DQ-01"], "SL-META-02": ["CFG-05"],
    "SL-META-03": ["SERV-01", "PROJ-01"], "SL-META-04": ["CFG-01"], "SL-META-05": ["CFG-04"],
    "SL-SEC-11": ["ENC-01"],
}


class NoAlias(yaml.SafeDumper):
    def ignore_aliases(self, data):
        return True


def dump(recs):
    return yaml.dump(recs, sort_keys=False, width=110, allow_unicode=True, Dumper=NoAlias)


def js_to_json(src):
    """The page's data is a JS literal: strip comments, quote the bare keys, drop trailing commas."""
    src = re.sub(r"/\*.*?\*/", "", src, flags=re.S)
    src = re.sub(r"([{,]\s*)(k|t|l|c|w|h|i|enforced):", r'\1"\2":', src)
    return re.sub(r",(\s*[\]}])", r"\1", src)


def block(html, start, end):
    s = html.index(start) + len(start) - 1
    return html[s:html.index(end, s) + 1]


def main(page):
    html = Path(page).read_text()
    cards = json.loads(js_to_json(block(html, "const ENTRIES = [", "];\n</script>")))
    gaps = json.loads(block(html, "const GAPS = {", "};"))
    assert len(cards) == 134, len(cards)
    assert set(MAP) | set(DROPPED) == set(range(1, 135)) and not set(MAP) & set(DROPPED)

    by_file, dropped = {}, []
    for n, c in enumerate(cards, 1):
        enforced = []
        for e in c["enforced"]:
            if e["type"] == "shift-left":
                enforced.append({"shift_left": e["ids"]})
            elif e["type"] == "gap":
                enforced.append({"proposed": e["id"]})
            else:
                enforced.append({e["type"]: e["text"]})
        fix = REWRITE.get(n, {})
        rec = {"id": f"BP-{n:03d}", "status": "draft", "since": "0.1.0", "kind": KIND[c["k"]],
               "title": fix.get("title", c["t"]), "why": fix.get("why", c["w"]),
               "how": {"binding": "aws-databricks", "text": c["h"]}}
        if c.get("i"):
            rec["instead"] = fix.get("instead", c["i"])
        rec["layers"] = [LAYER[x] for x in c["l"].split()]
        rec["components"] = c["c"].split()
        rec["enforced_by"] = enforced
        if n in DROPPED:
            rec["dropped"] = DROPPED[n]
            dropped.append(rec)
            continue
        rec["dac"], rec["adr"] = MAP[n]
        f = "canon" if c["k"] == "P" else rec["components"][0]
        by_file.setdefault(f, []).append(rec)

    comps = yaml.safe_load((OUT / "components.yaml").read_text())
    for f, recs in by_file.items():
        name = "The canon: principles every layer follows" if f == "canon" else comps[f]
        (OUT / f"{f}.yaml").write_text(f"# Practices: {name}. Normative: edit here.\n" + dump(recs))
    (OUT / "dropped.yaml").write_text("# Cards from the page that were not kept, each with the reason. Ids are never "
                                      "reused.\n" + dump(dropped))
    proposed = [{"id": k, "title": v[0], "stage": v[1], "catches": v[2], "dac": PROPOSED_DAC[k]}
                for k, v in sorted(gaps.items())]
    (OUT / "proposed-checks.yaml").write_text(
        "# Static checks the practices need that the shift-left bundle does not have yet. When the bundle ships one,\n"
        "# delete it here: the linter fails while an id is in both places.\n" + dump(proposed))
    kept = sum(map(len, by_file.values()))
    print(f"{kept} practices in {len(by_file)} files, {len(dropped)} dropped, {len(proposed)} proposed checks")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else str(Path.home() / "Engineering-Best-Practices.html"))
