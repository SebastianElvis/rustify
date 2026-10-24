#!/usr/bin/env python3
"""Replay the frozen base64 replacement against the pinned reference."""

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
WRAPPER = Path(__file__).resolve().parent
PROJECT = WRAPPER / "target"
RECOVERED = PROJECT / "recovered"
VERIFICATION = PROJECT / "verification"
RAW = VERIFICATION / "raw"
LOGS = VERIFICATION / "logs"
AGENT = ROOT / "work/evaluation/base64/agent"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def main():
    for directory in (RAW, LOGS, AGENT):
        directory.mkdir(parents=True, exist_ok=True)
    summary = {"status": "failed", "source_assisted_changes": False, "commands": []}
    try:
        freeze_path = RECOVERED / "evidence/freeze-manifest.json"
        freeze = json.loads(freeze_path.read_text())
        frozen = {"implementation/" + name.removeprefix("replacement/"): entry for name, entry in freeze["files"].items() if name.startswith("replacement/")}
        if not frozen:
            raise ValueError("The freeze contains no replacement files.")
        for name, entry in frozen.items():
            if digest(PROJECT / name) != entry["sha256"]:
                raise ValueError("A frozen replacement file changed: " + name)
        for path in (PROJECT / "implementation").rglob("*"):
            if path.is_file() and "target" not in path.relative_to(PROJECT / "implementation").parts and path.suffix == ".rs" and str(path.relative_to(PROJECT)) not in frozen:
                raise ValueError("The replacement contains an unfrozen Rust source file.")
        summary["frozen_files_verified"] = len(frozen)
        summary["freeze_manifest_sha256"] = digest(freeze_path)
        provenance = json.loads((RECOVERED / "provenance.json").read_text())
        if provenance["binary_sha256"] != freeze["reference_sha256"]:
            raise ValueError("The reference provenance differs from the freeze.")
        reference = ROOT / "work/downloads/base64"
        env = dict(os.environ, CARGO_TARGET_DIR=str(PROJECT / "implementation/target"))

        def command(args, label):
            result = subprocess.run(args, cwd=PROJECT / "implementation", env=env, capture_output=True, text=True)
            log = LOGS / (label + ".log")
            log.write_text(result.stdout + result.stderr)
            summary["commands"].append({"args": args, "returncode": result.returncode, "log": str(log.relative_to(ROOT)), "rustflags": env.get("RUSTFLAGS")})
            return result

        if not reference.exists() or digest(reference) != provenance["binary_sha256"]:
            result = command([sys.executable, str(ROOT / "scripts/fetch_reference.py")], "fetch-reference")
            result.check_returncode()
        if digest(reference) != provenance["binary_sha256"]:
            raise ValueError("The reference binary hash differs from provenance.")
        project = load("rustify_project", ROOT / "skills/rustify/scripts/project.py")
        for name in ("rust-design.md", "plan.json"):
            shutil.copyfile(WRAPPER / "agent-fixtures" / name, AGENT / name)
        state_path = RECOVERED / "state.json"
        if state_path.exists():
            previous = json.loads(state_path.read_text())
            if previous["target"]["sha256"] != provenance["binary_sha256"]:
                raise ValueError("The saved state identifies a different reference.")
            if previous.get("version") != 2 or previous["target"]["path"] != str(reference) or previous.get("work_dir") != str(AGENT):
                save(RAW / "state-before-relocation.json", previous)
                state_path.unlink()
        if not state_path.exists():
            project.init(PROJECT, reference, "cli", work_dir=AGENT)
        if set(path.name for path in PROJECT.iterdir()) != {"recovered", "implementation", "verification"}:
            raise ValueError("The target must contain exactly the three approved directories.")

        def checkpoint_through(phase):
            progress = project.status(PROJECT)
            while progress["next"] is not None and project.PHASES.index(progress["next"]) <= project.PHASES.index(phase):
                progress = project.checkpoint(PROJECT, progress["next"])
            return progress

        checkpoint_through("plan")
        for args, label in [(["cargo", "fmt", "--check"], "fmt"), (["cargo", "clippy", "--all-targets", "--", "-D", "warnings"], "clippy"), (["cargo", "test"], "unit"), (["cargo", "build", "--release"], "build")]:
            result = command(args, label)
            if result.returncode and platform.system() == "Darwin" and "linking with" in result.stderr:
                env["RUSTFLAGS"] = env.get("RUSTFLAGS", "") + " -C linker=/usr/bin/clang -C link-arg=-fuse-ld=/usr/bin/ld"
                result = command(args, label + "-apple-linker")
            result.check_returncode()
            if label == "unit":
                summary["unit_tests"] = sum(map(int, re.findall(r"test result: ok\. (\d+) passed", result.stdout)))
                if not summary["unit_tests"]:
                    raise ValueError("The unit gate reports no passing tests.")
        save(VERIFICATION / "checks.json", {"status": "passed", "commands": summary["commands"], "unit_tests": summary["unit_tests"]})
        checkpoint_through("implement")
        candidate = PROJECT / "implementation/target/release/base64"
        compare = load("rustify_compare", ROOT / "skills/rustify-validate/scripts/compare.py")
        challenge = load("rustify_challenge", ROOT / "scripts/challenge_cases.py").cases()
        upstream = json.loads((RECOVERED / "upstream-vectors.json").read_text())
        if upstream["source_sha256"] != provenance["source_sha256"]:
            raise ValueError("The upstream vectors identify a different source archive.")
        if len(upstream["cases"]) != 201 or len(upstream["expected"]) != 201:
            raise ValueError("The complete upstream vector set must contain 201 cases.")
        save(RAW / "challenge-cases.json", challenge)
        reports = {}
        for name, cases, executable in [("repeatability", challenge + upstream["cases"], reference), ("challenge", challenge, candidate), ("upstream", upstream["cases"], candidate)]:
            report = compare.compare(reference, executable, cases, name="base64")
            save(RAW / (name + ".json"), report)
            reports[name] = report
        assertions = []
        for case in reports["upstream"]["cases"]:
            expected = upstream["expected"][case["input"]["id"]]
            for side in ("reference", "candidate"):
                differences = [key for key, value in expected.items() if case[side][key] != value]
                assertions.append({"id": case["input"]["id"], "program": side, "expected": expected, "differences": differences, "passed": not differences and case[side]["error"] is None})
        expected_report = {"passed": sum(item["passed"] for item in assertions), "failed": sum(not item["passed"] for item in assertions), "cases": assertions}
        save(RAW / "upstream-expected.json", expected_report)
        summary.update({"reference_sha256": digest(reference), "candidate_sha256": digest(candidate), "challenge_cases": len(challenge), "upstream_vectors": len(upstream["cases"]), "comparison_cases": len(challenge) + len(upstream["cases"]), "expected_output_assertions": expected_report["passed"], "expected_output_failures": expected_report["failed"], "reports": {name: {key: report[key] for key in ("status", "passed", "failed")} for name, report in reports.items()}, "raw_reports": str(RAW.relative_to(ROOT))})
        summary["status"] = "passed" if all(report["status"] == "passed" for report in reports.values()) and expected_report["failed"] == 0 else "failed"
        combined = {**reports["challenge"], "status": summary["status"], "passed": reports["challenge"]["passed"] + reports["upstream"]["passed"], "failed": reports["challenge"]["failed"] + reports["upstream"]["failed"], "cases": reports["challenge"]["cases"] + reports["upstream"]["cases"]}
        save(VERIFICATION / "comparison.json", combined)
        if summary["status"] == "passed":
            summary["checkpoints"] = checkpoint_through("validate")
            if summary["checkpoints"]["next"] is not None:
                raise ValueError("The project checkpoints remain incomplete.")
        summary["layout_migration"] = "The migration changes paths only. Historical replacement/ names remain in the original freeze."
        summary["target_project"] = str(PROJECT.relative_to(ROOT))
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as error:
        summary["error"] = str(error)
    save(VERIFICATION / "summary.json", summary)
    print(json.dumps({key: summary[key] for key in ("status", "unit_tests", "challenge_cases", "upstream_vectors", "comparison_cases", "expected_output_assertions") if key in summary}))
    if "error" in summary:
        print(summary["error"], file=sys.stderr)
    return 0 if summary["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
