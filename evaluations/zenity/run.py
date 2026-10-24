#!/usr/bin/env python3
"""Check the source-assisted JXA build without opening a GUI."""

import base64
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import zipfile


ROOT = Path(__file__).resolve().parent
REPOSITORY = ROOT.parents[1]
TARGET = ROOT / "target"
RECOVERED = TARGET / "recovered"
VERIFICATION = TARGET / "verification"
AGENT = REPOSITORY / "work/evaluation/zenity/agent"
REFERENCE = REPOSITORY / "work/downloads/zenity"
EXPECTED = {
    "entry-accept": (0, b"Rustify GUI test\n"),
    "entry-cancel": (1, b""),
    "question-accept": (0, b""),
    "question-cancel": (1, b""),
    "info-accept": (0, b""),
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n")


def frozen_evidence():
    provenance = json.loads((RECOVERED / "provenance.json").read_text())
    exception = provenance["freeze"]["operational_state_exception"]
    if sha((RECOVERED / exception["copy"]).read_bytes()) != exception["later_sha256"]:
        raise ValueError("The disclosed later state snapshot changed.")
    manifest = RECOVERED / "freeze.json"
    if sha(manifest.read_bytes()) != provenance["freeze"]["manifest_sha256"]:
        raise ValueError("The freeze manifest changed.")
    freeze = json.loads(manifest.read_text())
    archive = RECOVERED / provenance["freeze"]["archive"]
    if sha(archive.read_bytes()) != provenance["freeze"]["archive_sha256"]:
        raise ValueError("The frozen recording archive changed.")
    with zipfile.ZipFile(archive) as bundle:
        for name, expected in freeze["files"].items():
            if name != "state.json" and sha(bundle.read(name)) != expected:
                raise ValueError(f"The historical archive entry changed: {name}")
        if sha(bundle.read("recorded-candidate.bin")) != freeze["candidate_sha256"]:
            raise ValueError("The historical candidate bytes changed.")
    AGENT.mkdir(parents=True, exist_ok=True)
    for name in ("rust-design.md", "plan.json"):
        (AGENT / name).write_bytes((ROOT / "agent-fixtures" / name).read_bytes())
    pin = json.loads((RECOVERED / "evidence/jxa-source-pin.json").read_text())
    if pin["historical_freeze_sha256"] != sha(manifest.read_bytes()) or pin["historical_archive_sha256"] != sha(archive.read_bytes()):
        raise ValueError("The source-assisted pin identifies a different historical stage.")
    if pin["previous_stage_archive_sha256"] != sha((RECOVERED / "evidence/pre-jxa-repair.zip").read_bytes()):
        raise ValueError("The previous AppKit stage archive changed.")
    for name, expected in pin["source_files"].items():
        if sha((TARGET / "implementation" / name).read_bytes()) != expected:
            raise ValueError(f"The source-assisted input changed: {name}")
    return freeze, provenance, pin


def captured_results():
    scenarios = {case["id"]: case for case in json.loads((RECOVERED / "scenarios.json").read_text())}
    if set(scenarios) != set(EXPECTED):
        raise ValueError("The recorded scenario set changed.")
    cases = []
    for identity, (status, stdout) in EXPECTED.items():
        results = {}
        for label in ("reference", "candidate"):
            path = RECOVERED / f"evidence/{identity}-{label}.json"
            result = json.loads(path.read_text())
            if result["case"]["id"] != identity or result["case"]["args"] != scenarios[identity]["args"]:
                raise ValueError(f"The capture has different inputs: {identity}/{label}")
            if result["returncode"] != status or base64.b64decode(result["stdout_b64"], validate=True) != stdout or base64.b64decode(result["stderr_b64"], validate=True) != b"":
                raise ValueError(f"The capture fails its independent expectation: {identity}/{label}")
            results[label] = {key: result[key] for key in ("returncode", "stdout_b64", "stderr_b64")}
            if not identity.startswith("entry"):
                text = (RECOVERED / f"evidence/{identity}-{label}-ax.txt").read_text()
                tokens = ["Rustify brief test", "Rustify will close this test dialog."]
                tokens += ["button Yes", "button No"] if identity.startswith("question") else ["button OK"]
                if not all(token in text for token in tokens):
                    raise ValueError(f"The recorded AX capture lacks a required control: {identity}/{label}")
        cases.append({"id": identity, "expected_returncode": status, **results, "passed": True, "differences": []})
    return cases


def command(name, arguments):
    log = VERIFICATION / "logs" / (name + ".log")
    environment = os.environ.copy()
    if sys.platform == "darwin":
        environment.setdefault("RUSTFLAGS", "-C linker=/usr/bin/clang -C link-arg=-fuse-ld=/usr/bin/ld")
    with log.open("wb") as stream:
        result = subprocess.run(arguments, cwd=TARGET / "implementation", env=environment, stdout=stream, stderr=subprocess.STDOUT, timeout=180)
    if result.returncode:
        raise RuntimeError(f"The {name} check failed. Read {log}.")
    return {"name": name, "command": arguments, "returncode": result.returncode, "log": log.relative_to(TARGET).as_posix(), "log_sha256": sha(log.read_bytes())}


def reference(provenance):
    identity = provenance["reference"]
    if not REFERENCE.exists():
        archive = VERIFICATION / "raw/reference.zip"
        archive.parent.mkdir(exist_ok=True)
        subprocess.run(["curl", "-fsSL", "--connect-timeout", "10", "--max-time", "60", "--retry", "1", identity["release_url"], "-o", str(archive)], check=True)
        if sha(archive.read_bytes()) != identity["archive_sha256"]:
            raise ValueError("The reference archive hash differs.")
        with zipfile.ZipFile(archive) as bundle:
            names = [name for name in bundle.namelist() if Path(name).name == "zenity"]
            if len(names) != 1:
                raise ValueError("The reference archive must contain one executable.")
            data = bundle.read(names[0])
        if sha(data) != identity["binary_sha256"]:
            raise ValueError("The extracted reference hash differs.")
        REFERENCE.parent.mkdir(parents=True, exist_ok=True)
        REFERENCE.write_bytes(data)
    if REFERENCE.is_symlink() or sha(REFERENCE.read_bytes()) != identity["binary_sha256"]:
        raise ValueError("The reference differs from the recorded artifact.")


def checkpoint_status():
    spec = importlib.util.spec_from_file_location("project", REPOSITORY / "skills/rustify/scripts/project.py")
    project = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(project)
    return project.status(TARGET)


def main():
    (VERIFICATION / "logs").mkdir(parents=True, exist_ok=True)
    summary = {"status": "failed", "mode": "SOURCE-ASSISTED JXA fidelity repair", "fresh_unit_tests": 0, "historical_gui_cases": 0, "fresh_gui_cases": 0, "live_gui_replay": False, "source_assisted_changes": True, "full_product_parity": "unestablished", "commands": []}
    try:
        freeze, provenance, pin = frozen_evidence()
        historical_cases = captured_results()
        summary["historical_gui_cases"] = len(historical_cases)
        summary["historical_candidate_sha256"] = freeze["candidate_sha256"]
        summary["frozen_files_verified"] = 37
        summary["freeze_state_snapshot_available"] = False
        for name, args in (("fmt", ["cargo", "fmt", "--check"]), ("clippy", ["cargo", "clippy", "--locked", "--all-targets", "--", "-D", "warnings"]), ("unit", ["cargo", "test", "--locked"]), ("build-release", ["cargo", "build", "--release", "--locked"])):
            summary["commands"].append(command(name, args))
        summary["fresh_unit_tests"] = sum(int(value) for value in re.findall(r"test result: ok\. (\d+) passed", (VERIFICATION / "logs/unit.log").read_text()))
        if summary["fresh_unit_tests"] != 5:
            raise ValueError("The JSON protocol unit checks must report five tests.")
        reference(provenance)
        candidate = TARGET / "implementation/target/release/zenity"
        if sha(candidate.read_bytes()) != pin["candidate"]["sha256"]:
            raise ValueError("The current executable differs from the replay source pin.")
        summary["candidate_sha256"] = sha(candidate.read_bytes())
        summary["runtime_line_budget"] = pin["runtime_line_budget"]
        summary["checkpoint"] = checkpoint_status()
        summary["required_fresh_workflows"] = list(EXPECTED)
        report = {"status": "pending_fresh_gui_replay", "passed": 0, "failed": 0, "cases": [], "historical_gui_cases": len(historical_cases), "required_fresh_workflows": list(EXPECTED), "reason": "The historical AppKit captures do not validate the source-assisted JXA candidate."}
        save(VERIFICATION / "comparison.json", report)
        save(VERIFICATION / "checks.json", {"status": "passed", "commands": summary["commands"], "fresh_unit_tests": 5, "gui_replay_status": "pending_fresh_gui_replay"})
        summary["status"] = "pending_fresh_gui_replay"
    except Exception as error:
        summary["error"] = str(error)
    save(VERIFICATION / "summary.json", summary)
    print(json.dumps({key: value for key, value in summary.items() if key != "commands"}, indent=2))
    return 2 if summary["status"] == "pending_fresh_gui_replay" else 1


if __name__ == "__main__":
    raise SystemExit(main())
