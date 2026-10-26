#!/usr/bin/env python3
"""Score a sqlite3 reconstruction against the pinned hardened reference."""

import base64
import fcntl
from pathlib import Path
import sys
import tempfile

import yaml

ROOT = Path(__file__).resolve().parent
sys.path[:0] = [str(ROOT), str(next(path for path in ROOT.parents if (path / "harness.py").is_file()))]
import harness
import cases
import generate
import runner
import upstream

PIN = yaml.safe_load((ROOT / "reference.yaml").read_text())
TIMEOUT = 30


def replay(reference, candidate, items):
    return harness.compare.compare(reference, candidate, items, TIMEOUT, "sqlite3")


def milestones(reference):
    groups = {"core": cases.core(), "extended": cases.extended(), "complete": cases.complete()}
    runner.reset()
    runner.invoke(reference, ["f.db", "CREATE TABLE t(a, b)", "INSERT INTO t VALUES(1, 'x'), (NULL, x'00')"])
    data = base64.b64encode((runner.SANDBOX / "f.db").read_bytes()).decode("ascii")
    for item in groups["complete"]:
        if "fixture.db" in item["args"]:
            item["files"] = {"fixture.db": data}
    return groups


def merge(*reports):
    rows = [row for report in reports for row in report["cases"]]
    failed = sum(not row["passed"] for row in rows)
    return {"status": "failed" if failed else "passed", "passed": len(rows) - failed, "failed": failed, "cases": rows}


def score(reference, candidate, project):
    runner.SANDBOX.parent.mkdir(parents=True, exist_ok=True)
    lock = open(runner.SANDBOX.with_suffix(".lock"), "w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        raise RuntimeError(f"Another sqlite scorer uses {runner.SANDBOX}.") from None
    groups, generated = milestones(reference), generate.cases()
    every = [item for items in groups.values() for item in items]
    sessions = {name: [item for item in cases.SESSIONS if item["milestone"] == name] for name in groups}
    reports = {"repeatability": merge(replay(reference, reference, every + generated), runner.sessions(reference, reference, cases.SESSIONS), runner.crossread(reference, reference, cases.CROSSREAD))}
    for name, items in groups.items():
        reports[f"replay-{name}"] = merge(replay(reference, candidate, items), runner.sessions(reference, candidate, sessions[name]))
    reports["generate-full"] = merge(replay(reference, candidate, generated))
    reports["generate-full"]["seed"] = generate.SEED
    reports["metamorphic-crossread"] = runner.crossread(reference, candidate, cases.CROSSREAD)
    downloads = harness.REPOSITORY / "work/downloads"
    downloads.mkdir(parents=True, exist_ok=True)
    archive = harness.load("build_reference", harness.REPOSITORY / "scripts/build_reference.py").fetch(upstream.SOURCE, downloads)
    files = {}
    for name, text in upstream.files(archive).items():
        report = upstream.evaluate(reference, candidate, name, text)
        if report["converted"]:
            reports[f"upstream-{Path(name).stem}"] = report
        files[name] = {key: report[key] for key in ("status", "passed", "failed", "tests", "converted", "unstable", "unmatched")}
    failed = sum(value["status"] != "passed" for value in files.values())
    reports["upstream-tests"] = {"status": "invalid" if any(value["status"] == "invalid" for value in files.values()) else "failed" if failed else "passed", "passed": len(files) - failed, "failed": failed, **{key: sum(value[key] for value in files.values()) for key in ("tests", "converted", "unstable", "unmatched")}, "files": files}
    failures = []
    with tempfile.TemporaryDirectory() as directory:
        wrong = Path(directory) / "sqlite3"
        wrong.write_text(f'#!/bin/sh\n"{reference}" "$@" | tr a-z A-Z\n')
        wrong.chmod(0o755)
        if replay(reference, wrong, groups["core"][:5])["status"] != "failed":
            failures.append("The wrong-output control passes.")
    return reports, failures


if __name__ == "__main__":
    raise SystemExit(harness.run("sqlite", PIN, score))
