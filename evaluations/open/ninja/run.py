#!/usr/bin/env python3
"""The evaluator scores a Ninja reconstruction against the pinned hardened reference."""

from pathlib import Path
import sys
import tempfile

import yaml

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(next(path for path in ROOT.parents if (path / "harness.py").is_file())))
sys.path.insert(0, str(ROOT))
import harness
import browse
import cases
import generate
import runner
import upstream

PIN = yaml.safe_load((ROOT / "reference.yaml").read_text())


def merge(parts):
    rows = [dict(row, id=f"{row['id']}-{suffix}") for suffix, part in parts.items() for row in part["cases"]]
    failed = sum(not row["passed"] for row in rows)
    return {"status": "failed" if failed else "passed", "passed": len(rows) - failed, "failed": failed, "cases": rows}


def score(reference, candidate, project):
    ref, cand = ("reference", reference), ("candidate", candidate)
    files = upstream.sources()
    milestones, units, generated = cases.milestones(), upstream.unit_scenarios(files), generate.scenarios()
    everything = [item for group in (*milestones.values(), *units.values(), generated) for item in group]
    reports = {"repeatability": runner.compare([ref], [ref], everything)}
    reports.update({f"replay-{name}": runner.compare([ref], [cand], items) for name, items in milestones.items()})
    # The persistence report alternates the programs between steps, so each program continues the logs of the other.
    multi = [item for items in milestones.values() for item in items if len(item["steps"]) > 1]
    reports["replay-persistence"] = merge({"reference-first": runner.compare([ref], [ref, cand], multi), "candidate-first": runner.compare([ref], [cand, ref], multi)})
    reports["generate-scenarios"] = runner.compare([ref], [cand], generated)
    for name, script in upstream.SCRIPTS.items():
        reports[f"upstream-{name}"] = upstream.python_report(reference, candidate, files, script)
    inventory = upstream.inventory(files)
    for name, items in units.items():
        reports[f"upstream-{name}"] = runner.compare([ref], [cand], items)
        reports[f"upstream-{name}"]["coverage"] = {"tests": inventory[f"src/{name}.cc"]["tests"], "tests_with_cases": len({item["id"].split("/")[1].split("-")[0] for item in items})}
    browse_control = browse.compare(reference, reference)
    reports["repeatability"]["browse"] = browse_control
    reports["repeatability"]["control_counts"] = {
        "legacy_repeatability": {key: reports["repeatability"][key] for key in ("passed", "failed")},
        "browse_repeatability": {key: browse_control[key] for key in ("passed", "failed")},
    }
    reports["replay-browse"] = browse.compare(reference, candidate)
    reports["replay-browse"]["raw_cases"] = reports["replay-browse"]["cases"]
    if browse_control["status"] != "passed" or any(
        row["expected"].get("error") or row["expected"].get("errors")
        or row["expected"]["supervisor"].get("error")
        or row["expected"]["supervisor"]["returncode"] != 0
        or not row["expected"].get("termination", {}).get("qualified")
        or not row["expected"]["supervisor"].get("termination", {}).get("qualified")
        for row in reports["replay-browse"]["cases"]
    ):
        reports["repeatability"]["status"] = "failed"
    failures = []
    with tempfile.TemporaryDirectory() as directory:
        wrong = Path(directory) / "ninja"
        wrong.write_text(f'#!/bin/sh\n"{reference}" "$@"\nstatus=$?\nrm -f .ninja_log\nexit $status\n')
        wrong.chmod(0o755)
        if runner.compare([ref], [("wrong", wrong)], milestones["core"][:1])["status"] != "failed":
            failures.append("The control that drops the build log passes.")
        wrong_browse = Path(directory) / "wrong-browse"
        wrong_browse.write_text("#!/bin/sh\nexit 0\n")
        wrong_browse.chmod(0o755)
        control = browse.compare(reference, wrong_browse)
        control["control_source"] = wrong_browse.read_bytes()
        browse_control["wrong_candidate_control"] = control
        if control["status"] != "failed":
            failures.append("The control without a browse service passes.")
    return reports, failures


if __name__ == "__main__":
    raise SystemExit(harness.run("ninja", PIN, score))
