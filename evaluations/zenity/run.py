#!/usr/bin/env python3
"""Score a zenity reconstruction from host-native GUI captures without opening a dialog."""

import base64
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import harness

ROOT = Path(__file__).resolve().parent
PIN = {
    "url": "https://github.com/ncruces/zenity/releases/download/v0.10.15/zenity_macos.zip",
    "archive_sha256": "4997ad32c70384e90e8e8bba42e8eddb35e7d8b9a752a7c4cd3e42c4be36ddb3",
    "member": "zenity",
    "sha256": "5f917a17b59bc5c516fb8173a21d13f4ac0d47850ab09cd7097e19bcdb5495c5",
}


def verify(directory, hashes):
    cases = json.loads((ROOT / "cases.json").read_text())
    review = json.loads((directory / "visual-review.json").read_text())
    if review["capture_method"] != "host-native CUA" or set(review["cases"]) != {case["id"] for case in cases}:
        raise ValueError("The visual review does not identify the five cases.")
    rows = []
    for case in cases:
        identity, expected, verdict = case["id"], case["expect"], review["cases"][case["id"]]
        if any(verdict.get(field) != "passed" for field in ("status", "focus", "title", "icon", "family", "controls")):
            raise ValueError(f"The visual parity review fails: {identity}")
        results = {}
        for role, binary_hash in hashes.items():
            result = json.loads((directory / f"{identity}-{role}.json").read_text())
            if result["case"]["args"] != case["args"] or result["executable_sha256"] != binary_hash or result["capture_method"] != "host-native CUA":
                raise ValueError(f"The capture has different inputs or a different executable: {identity}/{role}")
            if result["returncode"] != expected["returncode"] or any(base64.b64decode(result[field]) != base64.b64decode(expected[field]) for field in ("stdout_b64", "stderr_b64")):
                raise ValueError(f"The process result differs from the expectation: {identity}/{role}")
            for field, suffix in (("ax", "-ax.txt"), ("screenshot", ".png")):
                capture = directory / f"{identity}-{role}{suffix}"
                if result[field + "_file"] != capture.name or capture.is_symlink() or not capture.is_file() or harness.digest(capture.read_bytes()) != result[field + "_sha256"]:
                    raise ValueError(f"The raw capture is missing or changed: {capture.name}")
            ax = (directory / result["ax_file"]).read_text()
            if sorted(re.findall(r"(?m)^\s*\d+\s+button\s+(.+?)(?:,\s*ID:.*)?$", ax)) != sorted(expected["buttons"]):
                raise ValueError(f"The AX buttons differ from the expectation: {identity}/{role}")
            if any(flag in case["args"] and case["args"][case["args"].index(flag) + 1] not in ax for flag in ("--title", "--text")) or (identity.startswith("entry") and "text field" not in ax):
                raise ValueError(f"The AX capture lacks the original text or field: {identity}/{role}")
            results[role] = result
        equal = results["reference"]["screenshot_sha256"] == results["candidate"]["screenshot_sha256"]
        if not equal and not verdict.get("pointer_effect"):
            raise ValueError(f"The screenshot difference has no reviewed explanation: {identity}")
        rows.append({"id": identity, **results, "visual_review": verdict, "raw_screenshots_equal": equal, "passed": True, "differences": []})
    return {"status": "passed", "passed": len(rows), "failed": 0, "cases": rows}


def score(reference, candidate, project):
    directory = project / "verification/gui-captures"
    hashes = {"reference": PIN["sha256"], "candidate": harness.digest(candidate.read_bytes())}
    if not (directory / "visual-review.json").is_file():
        return {}, [f"The project has no GUI captures in {directory}."]
    return {"gui": verify(directory, hashes)}, []


if __name__ == "__main__":
    raise SystemExit(harness.run("zenity", PIN, score))
