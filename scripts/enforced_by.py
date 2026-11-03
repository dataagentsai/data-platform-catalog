# /// script
# requires-python = ">=3.9"
# dependencies = ["pyyaml"]
# ///
"""Write `enforced_by` on every DAC obligation (decision D12). Run after the bundle or proposed-checks.yaml change.

    uv run scripts/enforced_by.py

Generated, do not edit by hand:
  shift_left  checks in the shift-left bundle whose `dac:` names this obligation (the reverse of their links)
  proposed    checks in practices/proposed-checks.yaml whose `dac:` names it
Hand-written, kept as they are:
  runtime     true when the obligation's `test` runs against data or a running platform
  review      what a person checks in design or pull-request review, or null
  gap         what is not enforced yet, or null. Set to a default when there is no build-time check.
"""
import sys

import yaml

from lint import ROOT, load_obligations
from lint_practices import GAP_DEFAULT, bundle_dir, expected_enforced, load_bundle, load_part


class NoAlias(yaml.SafeDumper):
    def ignore_aliases(self, data):
        return True


def updated(rec, want):
    old = rec.get("enforced_by") or {}
    e = {"shift_left": want["shift_left"], "proposed": want["proposed"],
         "runtime": old.get("runtime", bool(rec.get("test"))), "review": old.get("review"), "gap": old.get("gap")}
    built = bool(e["shift_left"] or e["proposed"])
    if not built and not e["gap"]:
        e["gap"] = GAP_DEFAULT
    if built and e["gap"] == GAP_DEFAULT:
        e["gap"] = None
    return e


def main():
    bundle = load_bundle()
    if bundle is None:
        sys.exit(f"shift-left bundle not found at {bundle_dir()}; set SHIFT_LEFT_BUNDLE")
    want = expected_enforced(load_obligations(), bundle, load_part("proposed-checks"))
    changed = 0
    for f in sorted((ROOT / "dac" / "obligations").glob("*.yaml")):
        text = f.read_text()
        head = text.split("\n", 1)[0] + "\n"
        recs = yaml.safe_load(text)
        for r in recs:
            e = updated(r, want[r["id"]])
            changed += e != r.get("enforced_by")
            r.pop("enforced_by", None)
            r["enforced_by"] = e
        out = head + yaml.dump(recs, sort_keys=False, width=110, allow_unicode=True, Dumper=NoAlias)
        if out != text:
            f.write_text(out)
    print(f"enforced_by: {changed} obligations updated")


if __name__ == "__main__":
    main()
