#!/usr/bin/env python3
"""Run the pinned xh reconstruction evaluation from any directory."""

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tarfile
import zipfile


ROOT = Path(__file__).resolve().parent
REPOSITORY = ROOT.parents[1]
TARGET = ROOT / "target"
RECOVERED = TARGET / "recovered"
VERIFICATION = TARGET / "verification"
WORK = VERIFICATION / "raw"
AGENT = REPOSITORY / "work/evaluation/xh/agent"
REFERENCE = REPOSITORY / "work/downloads/xh"
ASSET_URL = "https://github.com/ducaale/xh/releases/download/v0.26.3/xh-v0.26.3-aarch64-apple-darwin.tar.gz"
ARCHIVE_SHA256 = "50d61bd755942752b054297a1612ec191654f137f8939673cda83c686cb5b0f2"
BINARY_SHA256 = "ea62f476d76bdfd401e56bdee8fb2630d447aeb843b7c5fdde8bcd3de86b391d"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n")


def reference():
    if not REFERENCE.exists():
        archive = WORK / "reference.tar.gz"
        subprocess.run(["curl", "-fsSL", "--connect-timeout", "10", "--max-time", "60", "--retry", "1", ASSET_URL, "-o", str(archive)], check=True)
        if sha(archive) != ARCHIVE_SHA256:
            raise ValueError("The reference archive hash differs from the pinned hash.")
        with tarfile.open(archive) as bundle:
            members = [item for item in bundle.getmembers() if item.isfile() and Path(item.name).name == "xh"]
            if len(members) != 1:
                raise ValueError("The reference archive must contain one xh executable.")
            data = bundle.extractfile(members[0]).read()
        if hashlib.sha256(data).hexdigest() != BINARY_SHA256:
            raise ValueError("The extracted binary hash differs from the pinned hash.")
        REFERENCE.parent.mkdir(parents=True, exist_ok=True)
        REFERENCE.write_bytes(data)
        REFERENCE.chmod(0o755)
    if REFERENCE.is_symlink() or sha(REFERENCE) != BINARY_SHA256:
        raise ValueError("The reference binary differs from the pinned artifact.")


def frozen_source():
    freeze = json.loads((RECOVERED / "freeze.json").read_text())
    with zipfile.ZipFile(RECOVERED / "evidence/binary-only-evidence.zip") as bundle:
        for name, expected in freeze["files"].items():
            if hashlib.sha256(bundle.read(name)).hexdigest() != expected:
                raise ValueError(f"The frozen file hash differs: {name}")
        AGENT.mkdir(parents=True, exist_ok=True)
        for name in ("rust-design.md", "plan.json"):
            if not (AGENT / name).exists():
                (AGENT / name).write_bytes(bundle.read(name))


def command(name, arguments, directory, records):
    log = VERIFICATION / "logs" / (name + ".log")
    environment = os.environ.copy()
    if sys.platform == "darwin":
        environment.setdefault("RUSTFLAGS", "-C linker=/usr/bin/clang -C link-arg=-fuse-ld=/usr/bin/ld")
    with log.open("wb") as stream:
        result = subprocess.run(arguments, cwd=directory, env=environment, stdout=stream, stderr=subprocess.STDOUT, timeout=180)
    records.append({"name": name, "command": arguments, "returncode": result.returncode, "log": log.relative_to(REPOSITORY).as_posix(), "log_sha256": sha(log)})
    if result.returncode:
        raise RuntimeError(f"The {name} check failed. Read {log}.")


def checkpoints():
    helper = REPOSITORY / "skills/rustify/scripts/project.py"
    spec = importlib.util.spec_from_file_location("project", helper)
    project = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(project)
    path = RECOVERED / "state.json"
    if path.exists():
        state = json.loads(path.read_text())
        if state["target"]["sha256"] != BINARY_SHA256:
            raise ValueError("The saved project uses a different reference.")
        state["target"]["path"] = str(REFERENCE)
        state["work_dir"] = str(AGENT)
        project.save(TARGET, state)
    else:
        project.init(TARGET, REFERENCE, "cli", work_dir=AGENT)
    for _ in project.PHASES:
        progress = project.status(TARGET)
        if progress["next"] is None:
            return progress
        project.checkpoint(TARGET, progress["next"])
    return project.status(TARGET)


def main():
    WORK.mkdir(parents=True, exist_ok=True)
    (VERIFICATION / "logs").mkdir(parents=True, exist_ok=True)
    summary = {"status": "failed", "reference_sha256": BINARY_SHA256, "commands": []}
    try:
        reference()
        frozen_source()
        replacement = TARGET / "implementation"
        for name, arguments in [
            ("fmt", ["cargo", "fmt", "--check"]),
            ("clippy", ["cargo", "clippy", "--locked", "--all-targets", "--", "-D", "warnings"]),
            ("rust-tests", ["cargo", "test", "--locked"]),
            ("build", ["cargo", "build", "--locked"]),
        ]:
            command(name, arguments, replacement, summary["commands"])
        command("comparison", [sys.executable, str(ROOT / "evaluate.py"), "--port", "0"], ROOT, summary["commands"])
        command("upstream", [sys.executable, str(ROOT / "upstream.py")], ROOT, summary["commands"])
        for name, filename in (("process", "comparison.json"), ("protocol", "comparison-protocol.json"), ("repeatability", "comparison-repeatability.json"), ("upstream", "upstream.json")):
            report = json.loads((WORK / filename).read_text())
            summary[name] = {key: report[key] for key in ("status", "passed", "failed")}
            if report["status"] != "passed" or report["failed"] != 0 or report["passed"] <= 0:
                raise ValueError(f"The {name} report failed.")
        report = json.loads((WORK / "comparison.json").read_text())
        compact = {key: report[key] for key in ("status", "passed", "failed", "executables")}
        compact["full_report"] = "raw/comparison.json"
        compact["cases"] = [{"id": item["input"]["id"], "passed": item["passed"], "differences": item["differences"]} for item in report["cases"]]
        save(VERIFICATION / "comparison.json", compact)
        candidate = replacement / "target/debug/xh"
        save(VERIFICATION / "checks.json", {"status": "passed", "commands": summary["commands"], "candidate_sha256": sha(candidate)})
        summary["rust_test_suites"] = [int(value) for value in re.findall(r"test result: ok\. (\d+) passed", (VERIFICATION / "logs/rust-tests.log").read_text())]
        summary["candidate_sha256"] = sha(candidate)
        summary["checkpoint"] = checkpoints()
        if summary["checkpoint"]["next"] is not None:
            raise ValueError("The project still has an incomplete checkpoint.")
        summary["status"] = "passed"
    except Exception as error:
        summary["error"] = str(error)
    save(VERIFICATION / "summary.json", summary)
    print(json.dumps({key: value for key, value in summary.items() if key != "commands"}, indent=2))
    return 0 if summary["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
