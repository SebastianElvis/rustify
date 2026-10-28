#!/usr/bin/env python3
"""Score a bzip2 reconstruction against the pinned hardened reference."""

import base64
from pathlib import Path
import random
import sys
import tarfile
import tempfile

import yaml

ROOT = Path(__file__).resolve().parent
sys.path[:0] = [str(ROOT), str(next(path for path in ROOT.parents if (path / "harness.py").is_file()))]
import harness
from cases import case, challenge, generate, text, upstream

PIN = yaml.safe_load((ROOT / "reference.yaml").read_text())
TIMEOUT = 30


def samples():
    """Read the upstream sample files from the pinned source archive."""
    downloads = harness.REPOSITORY / "work/downloads"
    downloads.mkdir(parents=True, exist_ok=True)
    archive = harness.load("build", harness.REPOSITORY / "eval/build.py").fetch(PIN["sources"][0], downloads)
    with tarfile.open(archive) as bundle:
        return {Path(item.name).name: bundle.extractfile(item).read() for item in bundle.getmembers() if item.isfile() and Path(item.name).name.startswith("sample")}


def summary(rows, extra=None):
    failed = sum(not row["passed"] for row in rows)
    return {"status": "failed" if failed else "passed", "passed": len(rows) - failed, "failed": failed, **(extra or {}), "cases": rows}


def compare(reference, candidate, groups):
    """Compare each program-name group and merge the results into one report."""
    parts = [harness.compare.compare(reference, candidate, items, TIMEOUT, name) for name, items in groups.items()]
    return summary([row for part in parts for row in part["cases"]], {"executables": parts[0]["executables"]})


def cross(reference, candidate):
    """Decompress the output of each program with the other program."""
    rng = random.Random(7)
    inputs = {"empty": b"", "byte": b"z", "text": text(rng, 40000), "noise": rng.randbytes(20000), "zeros": bytes(150000), "periodic": b"abc" * 70000}
    rows = []
    for name, data in inputs.items():
        for args in (["-1"], ["-5"], ["-9"], ["--exponential"]):
            for direction, first, second in (("candidate-to-reference", candidate, reference), ("reference-to-candidate", reference, candidate)):
                packed = harness.compare.run(first, "bzip2", case(name, args, data), TIMEOUT)
                unpacked = harness.compare.run(second, "bzip2", {"id": name, "args": ["-d"], "stdin_b64": packed["stdout_b64"]}, TIMEOUT)
                passed = not packed["error"] and not unpacked["error"] and packed["returncode"] == unpacked["returncode"] == 0 and base64.b64decode(unpacked["stdout_b64"]) == data
                rows.append({"id": f"{'exponential' if '--exponential' in args else 'block-size'}/{name}{''.join(args)}-{direction}", "returncodes": [packed["returncode"], unpacked["returncode"]], "compressed_sha256": harness.digest(base64.b64decode(packed["stdout_b64"])), "passed": passed})
    return summary(rows)


def score(reference, candidate, project):
    milestones = challenge()
    vectors, expected = upstream(samples())
    groups = {**milestones, "generate-options": {"bzip2": generate()}, **{name: {"bzip2": items} for name, items in vectors.items()}}
    everything = {}
    for group in groups.values():
        for name, items in group.items():
            everything.setdefault(name, []).extend(items)
    reports = {"repeatability": compare(reference, reference, everything)}
    reports.update({name: compare(reference, candidate, group) for name, group in groups.items()})
    reports["metamorphic-roundtrip"] = cross(reference, candidate)
    failures = [f"{row['input']['id']}/{side}" for row in reports["upstream-tests"]["cases"] for side in ("reference", "candidate") if row[side]["returncode"] or row[side]["error"] or row[side]["stderr_b64"] or base64.b64decode(row[side]["stdout_b64"]) != expected[row["input"]["id"]]]
    with tempfile.TemporaryDirectory() as directory:
        wrong = Path(directory) / "bzip2"
        wrong.write_text(f'#!/bin/sh\nexec "{reference}" -1 "$@"\n')
        wrong.chmod(0o755)
        if compare(reference, wrong, {"bzip2": milestones["replay-core"]["bzip2"][:3]})["status"] != "failed":
            failures.append("The wrong-level control passes.")
    return reports, failures


if __name__ == "__main__":
    raise SystemExit(harness.run("bzip2", PIN, score))
