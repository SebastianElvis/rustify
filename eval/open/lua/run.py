#!/usr/bin/env python3
"""Score a Lua 5.5.1 reconstruction against the pinned hardened reference."""

from pathlib import Path
import sys
import tempfile

import yaml

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(next(path for path in ROOT.parents if (path / "harness.py").is_file())))
sys.path.insert(0, str(ROOT))
import harness
from cases import milestones
import generate
import upstream

PIN = yaml.safe_load((ROOT / "reference.yaml").read_text())
TIMEOUT = 20


def score(reference, candidate, project):
    groups = {**milestones(), **generate.reports()}
    everything = [case for items in groups.values() for case in items]
    reports = {"repeatability": harness.compare.compare(reference, reference, everything, TIMEOUT, "lua")}
    reports.update({name: harness.compare.compare(reference, candidate, items, TIMEOUT, "lua") for name, items in groups.items()})
    reports["generate-cli"]["seed"] = reports["generate-core"]["seed"] = reports["generate-extended"]["seed"] = generate.SEED
    reports.update(upstream.evaluate(reference, candidate))
    failures = []
    with tempfile.TemporaryDirectory() as directory:
        wrong = Path(directory) / "lua"
        wrong.write_text(f'#!/bin/sh\nexec "{reference}" -e "print = function (...) io.write(\'wrong\\\\n\') end" "$@"\n')
        wrong.chmod(0o755)
        control = harness.compare.compare(reference, wrong, groups["replay-core"][:5], TIMEOUT, "lua")
        if control["status"] != "failed" or upstream.evaluate(reference, wrong, ["strings"])["upstream-strings"]["status"] != "failed":
            failures.append("The wrong-print control passes.")
    return reports, failures


if __name__ == "__main__":
    raise SystemExit(harness.run("lua", PIN, score))
