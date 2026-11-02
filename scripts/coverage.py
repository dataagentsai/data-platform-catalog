# /// script
# requires-python = ">=3.9"
# dependencies = ["pyyaml"]
# ///
"""Per concern: which ports a binding covers, how much the platform's own offering covers, and who fills the gap.

    uv run scripts/coverage.py slices/01-orders/binding-databricks.yaml > slices/01-orders/COVERAGE.md
"""
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lint  # noqa: E402

path = Path(sys.argv[1])
b = yaml.safe_load(path.read_text())
names = yaml.safe_load((lint.ROOT / "core" / "concerns.yaml").read_text())
cov = lint.coverage_by_concern(b, lint.load_ports())
word = {"full": "platform covers it", "partial": "platform covers part", "none": "platform has nothing",
        "unbound": "not bound in this slice"}
print(f"# Coverage by concern: {b['subject']['name']} on {b['subject']['platform']}\n")
print(f"Generated from `{path.name}` by `scripts/coverage.py`; do not edit by hand.\n")
print("| Concern | Port | Coverage | Gap filled by |\n|---|---|---|---|")
for c in sorted(names, key=lambda k: int(k[1:])):
    for port, level, filler in cov.get(c, [("(no port yet)", "unbound", "")]):
        print(f"| {c} {names[c]['name']} | {port} | {word[level]} | {filler or '-'} |")
counts = {k: sum(1 for x in b["bindings"].values() if x["coverage"] == k) for k in ("full", "partial", "none")}
print(f"\nPorts bound: {len(b['bindings'])}. The platform covers {counts['full']} fully, {counts['partial']} in part "
      f"and {counts['none']} not at all; every gap names who fills it.")
