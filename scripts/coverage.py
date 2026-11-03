# /// script
# requires-python = ">=3.9"
# dependencies = ["pyyaml", "jsonschema"]
# ///
"""Per concern: which ports a stack binds, how much the platform's own offering covers, and who fills the gap.

A stack (dbs/stacks/*.yaml) composes an engine layer, a cloud layer and a profile (decision M1, ADR-014).

    uv run scripts/coverage.py                       # every stack -> dbs/stacks/<name>.COVERAGE.md
    uv run scripts/coverage.py dbs/stacks/free-edition.yaml   # one stack to stdout
"""
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lint  # noqa: E402
import lint_shape  # noqa: E402

WORD = {"full": "platform covers it", "partial": "platform covers part", "none": "platform has nothing",
        "unbound": "not bound on this stack"}


def render(stack_name, stack, layers, ports):
    b = lint_shape.compose(stack, layers)
    names = yaml.safe_load((lint.ROOT / "core" / "concerns.yaml").read_text())
    by_port = {p["port"]: p for p in ports}
    cov = lint.coverage_by_concern(b, ports)
    layer_of = {}
    eng = lint_shape._layer_view(layers[("engine", stack["engine"]["layer"])], stack["engine"].get("profile"))[0]
    cld = (lint_shape._layer_view(layers[("cloud", stack["cloud"]["layer"])], stack["cloud"].get("profile"))[0]
           if stack.get("cloud") else {})
    for p in b["bindings"]:
        layer_of[p] = (stack["prefer"].get(p, "engine") if p in eng and p in cld else ("engine" if p in eng else "cloud"))
    parts = [f"engine {stack['engine']['layer']}" + (f" (profile {stack['engine']['profile']})"
                                                     if stack["engine"].get("profile") else "")]
    if stack.get("cloud"):
        parts.append(f"cloud {stack['cloud']['layer']}")
    out = [f"# Coverage by concern: {b['subject']['platform']}", "",
           f"Stack `{stack_name}`: {' + '.join(parts)}. Generated from `dbs/stacks/{stack_name}.yaml` by "
           "`scripts/coverage.py`; do not edit by hand.", "",
           "| Concern | Port | Layer | Coverage | Gap filled by |", "|---|---|---|---|---|"]
    for c in sorted(names, key=lambda k: int(k[1:])):
        for port, level, filler in cov.get(c, [("(no port yet)", "unbound", "")]):
            lay = layer_of.get(port, "-") if level != "unbound" else "-"
            out.append(f"| {c} {names[c]['name']} | {port} | {lay} | {WORD[level]} | {filler or '-'} |")
    counts = {k: sum(1 for x in b["bindings"].values() if x["coverage"] == k) for k in ("full", "partial", "none")}
    unbound = sorted(set(by_port) - set(b["bindings"]))
    out += ["", f"Ports bound: {len(b['bindings'])} of {len(by_port)}. The platform covers {counts['full']} fully, "
            f"{counts['partial']} in part and {counts['none']} not at all; every gap names who fills it.",
            f"Not bound on this stack: {', '.join(unbound) if unbound else 'none'}.",
            f"Accepted gaps: {', '.join(g['obligation'] for g in b['accepted_gaps']) or 'none'}."]
    return "\n".join(out) + "\n"


def main(argv):
    layers, ports = lint_shape.load_layers(), lint.load_ports()
    if argv:
        p = Path(argv[0])
        print(render(p.stem, yaml.safe_load(p.read_text()), layers, ports), end="")
        return
    for name, stack in lint_shape.load_stacks().items():
        (lint.ROOT / "dbs" / "stacks" / f"{name}.COVERAGE.md").write_text(render(name, stack, layers, ports))
        print(f"wrote dbs/stacks/{name}.COVERAGE.md")


if __name__ == "__main__":
    main(sys.argv[1:])
