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


def summary(rows, extra=None):
    failed = sum(not row["passed"] for row in rows)
    return {"status": "failed" if failed else "passed", "passed": len(rows) - failed, "failed": failed, **(extra or {}), "cases": rows}


def replay(reference, candidate, items):
    return harness.compare.compare(reference, candidate, items, TIMEOUT, "sqlite3")


def fixture(reference):
    """Let the reference write the database fixture of the deserialize case."""
    runner.reset()
    runner.invoke(reference, ["f.db", "CREATE TABLE t(a, b)", "INSERT INTO t VALUES(1, 'x'), (NULL, x'00')"])
    return base64.b64encode((runner.SANDBOX / "f.db").read_bytes()).decode("ascii")


def milestones(reference):
    groups = {"core": cases.core(), "extended": cases.extended(), "complete": cases.complete()}
    data = fixture(reference)
    for item in groups["complete"]:
        if "fixture.db" in item["args"]:
            item["files"] = {"fixture.db": data}
    return groups


def merge(*reports):
    rows = [row for report in reports for row in report["cases"]]
    return summary(rows, {key: sum(report.get(key, 0) for report in reports) for key in ("databases", "identical_databases")})


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
    failed = sum(value["status"] == "failed" for value in files.values())
    reports["upstream-tests"] = {"status": "failed" if failed else "passed", "passed": len(files) - failed, "failed": failed, **{key: sum(value[key] for value in files.values()) for key in ("tests", "converted", "unstable", "unmatched")}, "files": files}
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
