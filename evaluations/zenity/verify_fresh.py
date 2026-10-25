"""Validate source-bound CUA captures without opening a dialog."""

import base64
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(directory, recovered, pin_file):
    directory, recovered, pin_file = map(Path, (directory, recovered, pin_file))
    pin = json.loads(pin_file.read_text())
    pin_hash = digest(pin_file)
    baseline = datetime.fromisoformat(pin["created_utc"])
    reference_hash = json.loads((recovered / "freeze.json").read_text())["reference_sha256"]
    scenarios = {case["id"]: case for case in json.loads((recovered / "scenarios.json").read_text())}
    evidence_ids = {item["id"] for item in json.loads((recovered / "evidence.json").read_text())}
    expectations = {}
    for test in json.loads((recovered / "tests.json").read_text()):
        if test["origin"] != "observed" or not set(test["evidence"]) <= evidence_ids:
            raise ValueError("A GUI expectation lacks observed original evidence.")
        for identity in test["scenarios"]:
            if identity in expectations:
                raise ValueError("A GUI scenario has duplicate expectations.")
            expectations[identity] = test["expect"]
    if set(expectations) != set(scenarios) or len(scenarios) != 5:
        raise ValueError("The GUI tests must cover the five contracted scenarios.")
    review_path = directory / "visual-review.json"
    review = json.loads(review_path.read_text())
    if review["source_pin_sha256"] != pin_hash or review["capture_method"] != "host-native CUA" or set(review["cases"]) != set(scenarios):
        raise ValueError("The visual review does not identify the current source and cases.")
    files = {"visual-review.json": digest(review_path)}
    cases = []
    for identity, scenario in scenarios.items():
        expected = expectations[identity]
        verdict = review["cases"][identity]
        if any(verdict.get(field) != "passed" for field in ("status", "focus", "title", "icon", "family", "controls")):
            raise ValueError(f"The visual parity review fails: {identity}")
        results = {}
        for role, binary_hash in (("reference", reference_hash), ("candidate", pin["candidate"]["sha256"])):
            name = f"{identity}-{role}.json"
            path = directory / name
            result = json.loads(path.read_text())
            if result["case"]["id"] != identity or result["case"]["args"] != scenario["args"]:
                raise ValueError(f"The capture has different inputs: {identity}/{role}")
            if result["executable_sha256"] != binary_hash or result["capture_method"] != "host-native CUA":
                raise ValueError(f"The capture has a different executable or method: {identity}/{role}")
            captured = datetime.fromisoformat(result["captured_at_utc"])
            if captured.tzinfo is None or captured < baseline:
                raise ValueError(f"The capture predates the current source pin: {identity}/{role}")
            if role == "candidate" and result["source_pin_sha256"] != pin_hash:
                raise ValueError(f"The candidate capture has a stale source pin: {identity}")
            for field in ("returncode", "stdout_b64", "stderr_b64"):
                if field.endswith("_b64"):
                    actual = base64.b64decode(result[field], validate=True)
                    value = base64.b64decode(expected[field], validate=True)
                else:
                    actual, value = result[field], expected[field]
                if actual != value:
                    raise ValueError(f"The original-derived expectation fails: {identity}/{role}/{field}")
            for field, suffix in (("ax", "-ax.txt"), ("screenshot", ".png")):
                filename = f"{identity}-{role}{suffix}"
                capture = directory / filename
                if result[field + "_file"] != filename or capture.is_symlink() or not capture.is_file() or not capture.stat().st_size:
                    raise ValueError(f"The raw capture is missing or invalid: {filename}")
                if digest(capture) != result[field + "_sha256"]:
                    raise ValueError(f"The raw capture hash differs: {filename}")
                files[filename] = digest(capture)
            ax = (directory / result["ax_file"]).read_text()
            buttons = re.findall(r"(?m)^\s*\d+\s+button\s+(.+?)(?:,\s*ID:.*)?$", ax)
            if sorted(buttons) != sorted(expected["buttons"]):
                raise ValueError(f"The AX buttons differ from tests.json: {identity}/{role}")
            for flag in ("--title", "--text"):
                if flag in scenario["args"] and scenario["args"][scenario["args"].index(flag) + 1] not in ax:
                    raise ValueError(f"The AX capture lacks original text: {identity}/{role}/{flag}")
            if identity.startswith("entry") and "text field" not in ax:
                raise ValueError(f"The entry AX capture lacks its field: {identity}/{role}")
            image = (directory / result["screenshot_file"]).read_bytes()
            result["detected_screenshot_format"] = "png" if image.startswith(b"\x89PNG\r\n\x1a\n") else "jpeg" if image.startswith(b"\xff\xd8\xff") else None
            if result["detected_screenshot_format"] is None:
                raise ValueError("A screenshot has no supported image signature.")
            files[name] = digest(path)
            results[role] = result
        equal = results["reference"]["screenshot_sha256"] == results["candidate"]["screenshot_sha256"]
        pointer = verdict.get("pointer_effect", "")
        if not equal and (identity != "entry-accept" or not pointer):
            raise ValueError(f"The screenshot difference has no permitted external-pointer review: {identity}")
        cases.append({"id": identity, "expected": expected, **results, "visual_review": verdict, "raw_screenshots_equal": equal, "external_pointer_disclosure": pointer, "passed": True, "differences": []})
    return {"status": "passed", "passed": len(cases), "failed": 0, "cases": cases, "source_pin_sha256": pin_hash, "raw_evidence_hashes": files, "raw_identical_screenshot_pairs": sum(case["raw_screenshots_equal"] for case in cases), "method": "Independent tests.json expectations, pinned raw CUA captures, and explicit manual visual review", "live_gui_replay": False}
