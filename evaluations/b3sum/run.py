#!/usr/bin/env python3
"""Score a b3sum reconstruction against the pinned reference."""

import base64
import json
from pathlib import Path
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import harness

ROOT = Path(__file__).resolve().parent
PIN = {"url": "https://github.com/BLAKE3-team/BLAKE3/releases/download/1.8.7/b3sum_macos_x64_bin", "sha256": "97017f4477d872b24752a9bdbe48a6e0296fe1a66fc4787906c20c040b15c299"}


def vectors():
    data = json.loads((ROOT / "upstream-vectors.json").read_text())
    cases, expected = [], {}
    encode = lambda value: base64.b64encode(value).decode("ascii")
    for vector in data["cases"]:
        size = vector["input_len"]
        payload = bytes(i % 251 for i in range(size))
        for mode in ["hash", "keyed_hash", "derive_key"]:
            for length, seek in [(32, 0), (131, 0), (68, 63)]:
                identity = f"upstream-{size}-{mode}-{length}-{seek}"
                args = ["--raw", "--length", str(length), "--seek", str(seek)]
                case = {"id": identity, "args": args, "stdin_b64": encode(payload)}
                if mode == "keyed_hash":
                    args += ["--keyed", "input"]
                    case["stdin_b64"] = encode(data["key"].encode())
                    case["files"] = {"input": encode(payload)}
                elif mode == "derive_key":
                    args += ["--derive-key", data["context_string"]]
                cases.append(case)
                expected[identity] = bytes.fromhex(vector[mode])[seek:seek + length]
    return cases, expected


def score(reference, candidate, project):
    runtime = json.loads((ROOT / "cases.json").read_text())
    upstream, expected = vectors()
    reports = {
        "repeatability": harness.compare.compare(reference, reference, runtime, name="b3sum"),
        "runtime": harness.compare.compare(reference, candidate, runtime, name="b3sum"),
        "upstream": harness.compare.compare(reference, candidate, upstream, name="b3sum"),
    }
    failures = [f"{row['input']['id']}/{side}" for row in reports["upstream"]["cases"] for side in ("reference", "candidate") if row[side]["returncode"] or row[side]["error"] or row[side]["stderr_b64"] or base64.b64decode(row[side]["stdout_b64"]) != expected[row["input"]["id"]]]
    with tempfile.TemporaryDirectory() as directory:
        wrong = Path(directory) / "b3sum"
        wrong.write_text('#!/bin/sh\nprintf "wrong\\n"\n')
        wrong.chmod(0o755)
        if harness.compare.compare(reference, wrong, [runtime[0]], name="b3sum")["status"] != "failed":
            failures.append("The wrong-output control passes.")
    return reports, failures


if __name__ == "__main__":
    raise SystemExit(harness.run("b3sum", PIN, score))
