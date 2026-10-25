"""Score one agent-generated project for an evaluation track."""

import argparse
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import re
import subprocess
import tarfile
import zipfile

import yaml


REPOSITORY = Path(__file__).resolve().parents[1]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


compare = load("rustify_compare", REPOSITORY / "skills/rustify-validate/scripts/compare.py")
project_helper = load("rustify_project", REPOSITORY / "skills/rustify/scripts/project.py")


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(value, sort_keys=False))


def extract(data, member):
    if data.startswith(b"PK"):
        bundle = zipfile.ZipFile(io.BytesIO(data))
        items = [name for name in bundle.namelist() if not name.endswith("/") and member in (name, Path(name).name)]
        read = bundle.read
    else:
        bundle = tarfile.open(fileobj=io.BytesIO(data))
        items = [item for item in bundle.getmembers() if item.isfile() and member in (item.name, Path(item.name).name)]
        read = lambda item: bundle.extractfile(item).read()
    if len(items) != 1:
        raise ValueError("The reference archive must contain one matching executable.")
    return read(items[0])


def reference(track, pin):
    if "path" in pin:
        path = Path(pin["path"])
        if digest(path.read_bytes()) != pin["sha256"] or subprocess.check_output(["sw_vers", "-buildVersion"], text=True).strip() != pin["os_build"]:
            raise ValueError(f"The system reference differs from the pin. Use the operating system build {pin['os_build']}.")
        return path
    if "build" in pin:
        path = REPOSITORY / "work/references" / track / Path(pin["binary"]).name
        if not path.is_file() or digest(path.read_bytes()) != pin["sha256"]:
            load("build_reference", REPOSITORY / "scripts/build_reference.py").build(track)
        if digest(path.read_bytes()) != pin["sha256"]:
            raise ValueError(f"The hardened build differs from the pin. Use {pin['compiler']}.")
        return path
    path = REPOSITORY / "work/downloads" / track
    if path.is_file() and not path.is_symlink() and digest(path.read_bytes()) == pin["sha256"]:
        return path
    command = ["curl", "-fsSL", "--retry", "2", "--max-time", "120", pin["url"]]
    config = None
    if "token_url" in pin:
        token = json.loads(subprocess.check_output(["curl", "-fsSL", pin["token_url"]]))["token"]
        command += ["--config", "-"]
        config = f'header = "Authorization: Bearer {token}"\n'.encode()
    data = subprocess.run(command, input=config, capture_output=True, check=True).stdout
    if "archive_sha256" in pin:
        if digest(data) != pin["archive_sha256"]:
            raise ValueError("The reference archive hash differs from the pin.")
        data = extract(data, pin["member"])
    if digest(data) != pin["sha256"]:
        raise ValueError("The reference binary hash differs from the pin.")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    path.chmod(0o755)
    return path


def rust(project, logs):
    commands = []
    for label, args in (("fmt", ["fmt", "--check"]), ("clippy", ["clippy", "--locked", "--all-targets", "--", "-D", "warnings"]), ("test", ["test", "--locked"]), ("build", ["build", "--release", "--locked", "--message-format=json"])):
        result = subprocess.run(["cargo", *args], cwd=project / "implementation", capture_output=True, timeout=900)
        log = logs / f"{label}.log"
        log.parent.mkdir(parents=True, exist_ok=True)
        log.write_bytes(result.stdout + result.stderr)
        commands.append({"command": ["cargo", *args], "returncode": result.returncode, "log": str(log)})
        if result.returncode and label == "build":
            raise RuntimeError(f"The {label} check failed. Read {log}.")
    messages = [json.loads(line) for line in result.stdout.splitlines() if line.startswith(b"{")]
    binaries = sorted({item["executable"] for item in messages if item.get("executable") and "bin" in item["target"]["kind"]})
    if len(binaries) != 1:
        raise ValueError("The implementation must build exactly one executable.")
    tests = sum(map(int, re.findall(rb"test result: ok\. (\d+) passed", (logs / "test.log").read_bytes())))
    return Path(binaries[0]), {"commands": commands, "rust_tests": tests}


def run(track, pin, score):
    parser = argparse.ArgumentParser(description=f"Score a {track} reconstruction against the pinned reference.")
    parser.add_argument("--project", type=Path, default=REPOSITORY / "work/projects" / track)
    parser.add_argument("--output", type=Path, default=REPOSITORY / "work/evaluation" / track)
    args = parser.parse_args()
    project, output = args.project.resolve(), args.output.resolve()
    report = {"track": track, "project": str(project), "status": "failed"}
    try:
        executable = reference(track, pin)
        report["reference_sha256"] = pin["sha256"]
        if not (project / "implementation/Cargo.toml").is_file():
            raise ValueError(f"The project is missing. Reconstruct {executable} into {project}.")
        build = project / "implementation/target"
        report["freeze"] = {path.relative_to(project).as_posix(): digest(path.read_bytes()) for path in sorted(project.rglob("*")) if path.is_file() and build not in path.parents}
        try:
            report["checkpoints"] = project_helper.status(project)
        except (OSError, ValueError, KeyError) as error:
            report["checkpoints"] = {"error": str(error)}
        candidate, report["rust"] = rust(project, output / "logs")
        report["candidate_sha256"] = digest(candidate.read_bytes())
        linked = subprocess.run(["otool", "-L", str(candidate)], capture_output=True, text=True).stdout
        failures = [f"The {item['command'][1]} check failed. Read {item['log']}." for item in report["rust"].get("commands", []) if item["returncode"]] + [f"The candidate links the forbidden library {name}." for name in pin.get("forbidden_libraries", []) if f"/{name}.framework/" in linked or f"/lib{name}." in linked]
        if str(executable).encode() in candidate.read_bytes():
            failures.append("The candidate contains the reference path, so it can run the original.")
        reports, score_failures = score(executable, candidate, project)
        for name, value in reports.items():
            value["cases"] = [case if not case.get("passed", True) else {"id": case.get("id", case.get("input", {}).get("id")), "passed": True} for case in value.get("cases", [])]
            save(output / f"{name}.yaml", value)
        report["reports"] = {name: {key: value[key] for key in ("status", "passed", "failed")} for name, value in reports.items()}
        report["witnesses"] = {name: [{"id": identity, "feature": identity.split("/")[0], "differences": case.get("differences", case.get("failures")), "report": str(output / f"{name}.yaml")} for case in value.get("cases", []) if not case.get("passed", True) and (identity := case.get("id", case.get("input", {}).get("id")))] for name, value in reports.items()}
        report["failures"] = failures + score_failures
        report["status"] = "passed" if reports and all(value["status"] == "passed" for value in reports.values()) and not report["failures"] else "failed"
    except (OSError, ValueError, KeyError, RuntimeError, subprocess.SubprocessError) as error:
        report["error"] = str(error)
    save(output / "report.yaml", report)
    print(yaml.safe_dump({key: value for key, value in report.items() if key != "freeze"}, sort_keys=False), end="")
    return 0 if report["status"] == "passed" else 1
