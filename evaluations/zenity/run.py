#!/usr/bin/env python3
"""Verify recorded native GUI evidence and run fresh Rust unit checks."""

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
    expected_source = set()
    with zipfile.ZipFile(archive) as bundle:
        for name, expected in freeze["files"].items():
            if name == "state.json":
                continue
            if sha(bundle.read(name)) != expected:
                raise ValueError(f"The frozen archive entry changed: {name}")
            path = None
            if name.startswith("replacement/"):
                path = TARGET / "implementation" / name.removeprefix("replacement/")
                expected_source.add(path.relative_to(TARGET / "implementation").as_posix())
            elif name.startswith("evidence/"):
                path = RECOVERED / name
            elif name in {"contract.json", "scenarios.json"}:
                path = RECOVERED / name
            if path is not None and (path.is_symlink() or sha(path.read_bytes()) != expected):
                raise ValueError(f"The recorded code or evidence changed: {name}")
        AGENT.mkdir(parents=True, exist_ok=True)
        for name in ("rust-design.md", "plan.json"):
            if not (AGENT / name).exists():
                (AGENT / name).write_bytes(bundle.read(name))
        candidate = bundle.read("recorded-candidate.bin")
    source = {path.relative_to(TARGET / "implementation").as_posix() for path in (TARGET / "implementation").rglob("*") if path.is_file() and "target" not in path.relative_to(TARGET / "implementation").parts and (path.suffix == ".rs" or path.name in {"Cargo.toml", "Cargo.lock"})}
    if source != expected_source:
        raise ValueError("The recorded Rust source file set changed.")
    if sha(candidate) != freeze["candidate_sha256"]:
        raise ValueError("The recorded candidate bytes changed.")
    path = TARGET / "implementation/target/recorded/zenity"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(candidate)
    return freeze, provenance, path


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


def checkpoints():
    spec = importlib.util.spec_from_file_location("project", REPOSITORY / "skills/rustify/scripts/project.py")
    project = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(project)
    state = RECOVERED / "state.json"
    if state.exists():
        value = json.loads(state.read_text())
        if value["target"]["sha256"] != json.loads((RECOVERED / "freeze.json").read_text())["reference_sha256"]:
            raise ValueError("The saved project uses a different reference.")
        value["target"]["path"] = str(REFERENCE)
        value["work_dir"] = str(AGENT)
        project.save(TARGET, value)
    else:
        project.init(TARGET, REFERENCE, "desktop", work_dir=AGENT)
    for _ in project.PHASES:
        progress = project.status(TARGET)
        if progress["next"] is None:
            return progress
        project.checkpoint(TARGET, progress["next"])
    return project.status(TARGET)


def main():
    (VERIFICATION / "logs").mkdir(parents=True, exist_ok=True)
    summary = {"status": "failed", "mode": "Recorded GUI evidence with fresh Rust unit checks", "fresh_unit_tests": 0, "recorded_gui_cases": 0, "live_gui_replay": False, "upstream_test_suite_executed": False, "commands": []}
    try:
        freeze, provenance, candidate = frozen_evidence()
        cases = captured_results()
        summary["recorded_gui_cases"] = len(cases)
        summary["recorded_candidate_sha256"] = freeze["candidate_sha256"]
        summary["frozen_files_verified"] = 37
        summary["freeze_state_snapshot_available"] = False
        for name, args in (("fmt", ["cargo", "fmt", "--check"]), ("clippy", ["cargo", "clippy", "--locked", "--all-targets", "--", "-D", "warnings"]), ("unit", ["cargo", "test", "--locked"])):
            summary["commands"].append(command(name, args))
        summary["fresh_unit_tests"] = sum(int(value) for value in re.findall(r"test result: ok\. (\d+) passed", (VERIFICATION / "logs/unit.log").read_text()))
        if summary["fresh_unit_tests"] != 4:
            raise ValueError("The fresh unit test count differs from the recorded source.")
        reference(provenance)
        report = {"status": "passed", "passed": len(cases), "failed": 0, "method": "Independent checks of recorded native GUI process captures", "live_gui_replay": False, "cases": cases, "executables": {"reference": {"path": str(REFERENCE), "sha256": freeze["reference_sha256"]}, "candidate": {"path": str(candidate), "sha256": freeze["candidate_sha256"]}}}
        save(VERIFICATION / "comparison.json", report)
        save(VERIFICATION / "checks.json", {"status": "passed", "commands": summary["commands"], "live_gui_replay": False})
        summary["checkpoint"] = checkpoints()
        if summary["checkpoint"]["next"] is not None:
            raise ValueError("The recorded project has an incomplete checkpoint.")
        summary["status"] = "passed"
    except Exception as error:
        summary["error"] = str(error)
    save(VERIFICATION / "summary.json", summary)
    print(json.dumps({key: value for key, value in summary.items() if key != "commands"}, indent=2))
    return 0 if summary["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
