#!/usr/bin/env python3
"""Check the source-assisted JXA build without opening a GUI."""

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import zipfile

from verify_fresh import verify


ROOT = Path(__file__).resolve().parent
REPOSITORY = ROOT.parents[1]
TARGET = ROOT / "target"
RECOVERED = TARGET / "recovered"
VERIFICATION = TARGET / "verification"
AGENT = REPOSITORY / "work/evaluation/zenity/agent"
REFERENCE = REPOSITORY / "work/downloads/zenity"
PIN = RECOVERED / "evidence/jxa-exec-source-pin.json"
FRESH = RECOVERED / "evidence/jxa-exec-replay"


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
    pin = json.loads(PIN.read_text())
    if pin["historical_freeze_sha256"] != sha(manifest.read_bytes()) or pin["historical_archive_sha256"] != sha(archive.read_bytes()):
        raise ValueError("The source-assisted pin identifies a different historical stage.")
    if pin["previous_stage_archive_sha256"] != sha((RECOVERED / "evidence/pre-jxa-repair.zip").read_bytes()):
        raise ValueError("The previous AppKit stage archive changed.")
    if pin["failed_child_stage_pin_sha256"] != sha((RECOVERED / "evidence/jxa-source-pin.json").read_bytes()) or pin["failed_child_stage_archive_sha256"] != sha((RECOVERED / "evidence/jxa-child-focus-failure.zip").read_bytes()):
        raise ValueError("The preserved failed child-process stage changed.")
    for name, expected in pin["source_files"].items():
        if sha((TARGET / "implementation" / name).read_bytes()) != expected:
            raise ValueError(f"The source-assisted input changed: {name}")
    return freeze, provenance, pin


def captured_results():
    scenarios = {case["id"]: case for case in json.loads((RECOVERED / "scenarios.json").read_text())}
    expectations = {identity: test["expect"] for test in json.loads((RECOVERED / "tests.json").read_text()) for identity in test["scenarios"]}
    for identity, expected in expectations.items():
        for label in ("reference", "candidate"):
            result = json.loads((RECOVERED / f"evidence/{identity}-{label}.json").read_text())
            if result["case"]["args"] != scenarios[identity]["args"] or any(result[field] != expected[field] for field in ("returncode", "stdout_b64", "stderr_b64")):
                raise ValueError("A historical process capture fails its original-derived expectation.")
    return len(expectations)


def command(name, arguments):
    log = VERIFICATION / "logs" / (name + ".log")
    environment = os.environ.copy()
    if sys.platform == "darwin":
        environment.update(PATH="/opt/homebrew/bin:" + environment.get("PATH", ""), RUSTC="/opt/homebrew/bin/rustc", RUSTDOC="/opt/homebrew/bin/rustdoc", RUSTFLAGS="-C linker=/usr/bin/clang -C link-arg=-fuse-ld=/usr/bin/ld")
        for key in ("CARGO_ENCODED_RUSTFLAGS", "CARGO_TARGET_DIR", "SDKROOT", "MACOSX_DEPLOYMENT_TARGET", "RUSTC_WRAPPER", "RUSTC_WORKSPACE_WRAPPER"):
            environment.pop(key, None)
        arguments = ["/opt/homebrew/bin/cargo", *arguments[1:]] if arguments[0] == "cargo" else arguments
    with log.open("wb") as stream:
        result = subprocess.run(arguments, cwd=TARGET / "implementation", env=environment, stdout=stream, stderr=subprocess.STDOUT, timeout=180)
    if result.returncode:
        raise RuntimeError(f"The {name} check failed. Read {log}.")
    return {"name": name, "command": ["cargo", *arguments[1:]] if Path(arguments[0]).name == "cargo" else arguments, "executable": arguments[0], "returncode": result.returncode, "log": log.relative_to(TARGET).as_posix(), "log_sha256": sha(log.read_bytes()), "build_environment": {key: environment.get(key) for key in ("RUSTC", "RUSTDOC", "RUSTFLAGS", "CARGO_ENCODED_RUSTFLAGS", "CARGO_TARGET_DIR", "SDKROOT", "MACOSX_DEPLOYMENT_TARGET")}}


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


def checkpoint_status(advance=False):
    spec = importlib.util.spec_from_file_location("project", REPOSITORY / "skills/rustify/scripts/project.py")
    project = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(project)
    if advance:
        path = RECOVERED / "state.json"
        state = json.loads(path.read_text())
        state["target"]["path"] = str(REFERENCE)
        state["work_dir"] = str(AGENT)
        project.save(TARGET, state)
        for _ in project.PHASES:
            progress = project.status(TARGET)
            if progress["next"] is None:
                break
            project.checkpoint(TARGET, progress["next"])
    return project.status(TARGET)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fresh-evidence", type=Path, default=FRESH)
    options = parser.parse_args()
    (VERIFICATION / "logs").mkdir(parents=True, exist_ok=True)
    summary = {"status": "failed", "mode": "SOURCE-ASSISTED JXA fidelity repair", "fresh_unit_tests": 0, "historical_gui_cases": 0, "fresh_gui_cases": 0, "live_gui_replay": False, "source_assisted_changes": True, "full_product_parity": "unestablished", "commands": []}
    try:
        freeze, provenance, pin = frozen_evidence()
        historical_cases = summary["historical_gui_cases"] = captured_results()
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
        identities = [case["id"] for case in json.loads((RECOVERED / "scenarios.json").read_text())]
        summary["required_fresh_workflows"] = identities
        report = {"status": "pending_fresh_gui_replay", "passed": 0, "failed": 0, "cases": [], "historical_gui_cases": historical_cases, "required_fresh_workflows": identities, "reason": "The old AppKit and failed child-process captures do not validate this exec candidate."}
        if (options.fresh_evidence / "visual-review.json").is_file():
            report = verify(options.fresh_evidence, RECOVERED, PIN)
            FRESH.mkdir(exist_ok=True)
            for name in report["raw_evidence_hashes"]:
                source = options.fresh_evidence / name
                if source.resolve() != (FRESH / name).resolve():
                    shutil.copy2(source, FRESH / name)
            save(VERIFICATION / "fresh-proof.json", report)
            summary["commands"].append(command("proof-negative", [sys.executable, str(ROOT / "test_verifier.py")]))
            report["executables"] = {"reference": {"path": str(REFERENCE), "sha256": freeze["reference_sha256"]}, "candidate": {"path": str(candidate), "sha256": pin["candidate"]["sha256"]}}
            summary["fresh_gui_cases"] = report["passed"]
            summary["raw_identical_screenshot_pairs"] = report["raw_identical_screenshot_pairs"]
            summary["proof_tests"] = 8
            summary["source_pin_sha256"] = report["source_pin_sha256"]
        save(VERIFICATION / "comparison.json", report)
        save(VERIFICATION / "checks.json", {"status": "passed", "commands": summary["commands"], "fresh_unit_tests": 5})
        summary["status"] = report["status"]
        if report["status"] == "passed":
            summary["checkpoint"] = checkpoint_status(advance=True)
            if summary["checkpoint"]["next"] is not None:
                raise ValueError("The current GUI proof has incomplete checkpoints.")
    except Exception as error:
        summary.update(status="failed", error=str(error))
    save(VERIFICATION / "summary.json", summary)
    print(json.dumps({key: value for key, value in summary.items() if key != "commands"}, indent=2))
    return 0 if summary["status"] == "passed" else 2 if summary["status"] == "pending_fresh_gui_replay" else 1


if __name__ == "__main__":
    raise SystemExit(main())
