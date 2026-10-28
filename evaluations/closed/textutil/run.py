#!/usr/bin/env python3
"""Score a textutil reconstruction against the pinned macOS system binary."""

from concurrent.futures import ThreadPoolExecutor
import base64
import datetime
import os
from pathlib import Path
import plistlib
import re
import struct
import subprocess
import sys
import tempfile
import time

import yaml

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(next(path for path in ROOT.parents if (path / "harness.py").is_file())))
import harness
from cases import reports as case_reports
import parsers

PIN = yaml.safe_load((ROOT / "reference.yaml").read_text())
ENV = {"LC_ALL": "C", "LANG": "C", "TZ": "UTC", "PATH": "/usr/bin:/bin"}
APPLE_EPOCH = 978307200
REPEATS = 3


def execute(executable, case, timeout=60):
    """Run the steps of one case in a fresh folder and capture the view: process results and files."""
    executable = Path(executable).resolve()
    profile = f'(version 1)(allow default)(deny process-exec)(allow process-exec (literal "{executable}") (literal "/bin/sh") (literal "/bin/bash") (literal "/bin/dash"))'
    result = {"steps": [], "files": {}, "window": [time.time(), None], "error": None}
    with tempfile.TemporaryDirectory(prefix="rustify-") as directory:
        root = Path(directory)
        for filename, data in case["files"].items():
            (root / filename).parent.mkdir(parents=True, exist_ok=True)
            (root / filename).write_bytes(base64.b64decode(data))
        for args in case["steps"]:
            try:
                process = subprocess.run(["/usr/bin/sandbox-exec", "-p", profile, str(executable), *args], cwd=root, env={**ENV, "HOME": directory}, input=base64.b64decode(case.get("stdin_b64", "")), capture_output=True, timeout=timeout)
                result["steps"].append({"returncode": process.returncode, "stdout_b64": base64.b64encode(process.stdout).decode(), "stderr_b64": base64.b64encode(process.stderr).decode()})
            except subprocess.TimeoutExpired:
                result["error"] = "The process exceeded the time limit."
                break
        result["window"][1] = time.time()
        try:
            result["files"] = harness.compare.capture_files(root)
        except (OSError, ValueError) as error:
            result["error"] = str(error)
    return result


def zip_times(data, window):
    """Variable field: textutil stamps each docx and odt zip entry with the wall clock in the TZ zone."""
    data, low, high = bytearray(data), window[0] - 2, window[1] + 2
    offsets = [(i + 10) for i in range(len(data) - 30) if data[i:i + 4] == b"PK\x03\x04"] + [(i + 12) for i in range(len(data) - 46) if data[i:i + 4] == b"PK\x01\x02"]
    for offset in offsets:
        clock, day = struct.unpack_from("<HH", data, offset)
        try:
            stamp = datetime.datetime(1980 + (day >> 9), (day >> 5) & 15, day & 31, clock >> 11, (clock >> 5) & 63, (clock & 31) * 2, tzinfo=datetime.timezone.utc).timestamp()
        except ValueError:
            continue
        if low <= stamp <= high:
            data[offset:offset + 4] = b"\0\0\0\0"
    return bytes(data)


def response_times(data, window):
    """Variable field: each web archive subresource keeps an archived NSURLResponse with its creation time."""
    try:
        resources = plistlib.loads(data).get("WebSubresources", [])
    except Exception:
        return data
    for resource in resources:
        try:
            archive = plistlib.loads(resource["WebResourceResponse"])
            objects = archive["$objects"]
            value = objects[objects[archive["$top"]["WebResourceResponse"].data]["__nsurlrequest_proto_prop_obj_1"].data]
        except Exception:
            continue
        if isinstance(value, float) and window[0] - 1 <= value + APPLE_EPOCH <= window[1] + 1:
            data = data.replace(b"\x23" + struct.pack(">d", value), b"\x23" + bytes(8))
    return data


def log_lines(data, window):
    """Variable fields: NSLog prefixes carry the wall clock, the process id, and the thread id.
    An uncaught exception prints a call stack whose addresses move with ASLR."""
    def stamp(match):
        moment = datetime.datetime.strptime(match.group(1).decode(), "%Y-%m-%d %H:%M:%S.%f").replace(tzinfo=datetime.timezone.utc).timestamp()
        return b"<time> textutil[<pid>:<tid>] " if window[0] - 1 <= moment <= window[1] + 1 else match.group(0)
    data = re.sub(rb"(?m)^(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d\.\d{3}) textutil\[\d+:\d+\] ", stamp, data)
    return re.sub(rb"(?m)^(\t\d+ +\S+ +)0x[0-9a-f]{16}( )", rb"\1<address>\2", data)


def normal(data, window):
    if data.startswith(b"PK\x03\x04"):
        return zip_times(data, window)
    if data.startswith(b"bplist00"):
        return response_times(data, window)
    return data


def view(result):
    """Return the comparable view after the declared variable-field rules."""
    window = result["window"]
    decode = lambda value: harness.digest(normal(base64.b64decode(value), window))
    steps = [(step["returncode"], decode(step["stdout_b64"]), log_lines(base64.b64decode(step["stderr_b64"]), window)) for step in result["steps"]]
    return {"steps": steps, "files": {path: (decode(item["data_b64"]), item["mode"]) for path, item in result["files"].items()}, "error": result["error"]}


def differ(left, right):
    a, b = view(left), view(right)
    differences = [f"step{index + 1}.{field}" for index, (x, y) in enumerate(zip(a["steps"], b["steps"])) for field, p, q in zip(("returncode", "stdout", "stderr"), x, y) if p != q]
    differences += ["steps"] * (len(a["steps"]) != len(b["steps"])) + ["files"] * (a["files"] != b["files"])
    return differences + ["execution_error"] * bool(left["error"] or right["error"])


def relation(entry):
    """Metamorphic relation: LF text with a final newline survives txt, then any format, then txt."""
    if not re.search(r"/roundtrip-txt-(simple|unicode)$", entry["input"]["id"]):
        return entry
    for side in ("reference", "candidate"):
        files = entry[side]["files"]
        if files.get("back.txt", {}).get("data_b64") != entry["input"]["files"]["in.txt"]:
            entry["differences"].append(f"relation.{side}")
    entry["passed"] = not entry["differences"]
    return entry


def entry(case, reference, candidate):
    differences = differ(reference, candidate)
    return relation({"input": case, "reference": reference, "candidate": candidate, "differences": differences, "passed": not differences})


def report(rows):
    return {"status": "failed" if any(not row["passed"] for row in rows) or not rows else "passed", "passed": sum(row["passed"] for row in rows), "failed": sum(not row["passed"] for row in rows), "cases": rows}


def score(reference, candidate, project, workers=os.cpu_count()):
    groups = case_reports()
    everything = [case for rows in groups.values() for case in rows]
    with ThreadPoolExecutor(workers) as pool:
        originals = list(pool.map(lambda case: [execute(reference, case) for _ in range(REPEATS)], everything))
        results = list(pool.map(lambda case: execute(candidate, case), everything))
    runs = {case["id"]: (originals[index], results[index]) for index, case in enumerate(everything)}
    reports = {name: report([entry(case, runs[case["id"]][0][0], runs[case["id"]][1]) for case in rows]) for name, rows in groups.items()}
    reports["repeatability"] = report([entry(case, runs[case["id"]][0][0], again) for case in everything for again in runs[case["id"]][0][1:]])
    reports["parse-outputs"], failures = parsers.check(everything, runs)
    with tempfile.TemporaryDirectory() as directory:
        wrong = Path(directory) / "textutil"
        wrong.write_text('#!/bin/sh\nprintf "wrong\\n"\n')
        wrong.chmod(0o755)
        control = groups["surface-manual"][:3]
        if all(not differ(runs[case["id"]][0][0], execute(wrong, case)) for case in control):
            failures.append("The wrong-output control passes.")
        wrapper = Path(directory) / "wrapper"
        wrapper.write_text(f'#!/bin/sh\nexec {reference} "$@"\n')
        wrapper.chmod(0o755)
        if all(not differ(runs[case["id"]][0][0], execute(wrapper, case)) for case in control):
            failures.append("The framework-wrapper control passes.")
    return reports, failures


if __name__ == "__main__":
    raise SystemExit(harness.run("textutil", PIN, score))
