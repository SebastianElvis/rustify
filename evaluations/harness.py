"""Score one agent-generated project for an evaluation track."""

import argparse
import hashlib
import importlib.util
import io
import json, os
from pathlib import Path
import re
import subprocess
import sys
import tarfile
import zipfile

import yaml


REPOSITORY = Path(__file__).resolve().parents[1]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    exec(compile(path.read_bytes(), str(path), "exec"), module.__dict__)
    return module


compare = load("rustify_compare", REPOSITORY / "skills/rustify-probe/scripts/compare.py")
project_helper = load("rustify_project", REPOSITORY / "skills/rustify/scripts/project.py")


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(value, sort_keys=False))


def freeze(project, ignored=(), binaries=()):
    hashes = {path.relative_to(project).as_posix(): digest(path.read_bytes()) for path in sorted(project.rglob("*")) if path.is_file() and not set(ignored).intersection(path.relative_to(project).parts) and path.relative_to(project).parts[:2] != ("implementation", "target")}
    return {**hashes, **{str(path): [digest(path.read_bytes()), path.stat().st_mode, any(item.is_symlink() for item in (path, *path.parents))] for path in binaries}}


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


def rust(project, logs, candidate=None):
    commands = []
    for label, args in (("fmt", ["fmt", "--check"]), ("clippy", ["clippy", "--locked", "--all-targets", "--", "-D", "warnings"]), ("test", ["test", "--locked"]), ("pedantic", ["clippy", "--locked", "--", "-W", "clippy::pedantic"]), ("build", ["build", "--release", "--locked", "--message-format=json"])):
        if label == "build" and candidate is not None:
            continue
        result, error, resources = compare.execute(["cargo", *args], cwd=project / "implementation", env={**os.environ, "CARGO_BUILD_JOBS": "1", **({"CARGO_TARGET_DIR": str(logs / "target")} if candidate else {})}, timeout=900, memory_mib=2048, process_limit=32)
        returncode = result.returncode or int(error is not None)
        log = logs / f"{label}.log"
        log.parent.mkdir(parents=True, exist_ok=True)
        log.write_bytes(result.stdout + result.stderr + (error.encode() if error else b""))
        commands.append({"command": ["cargo", *args], "returncode": returncode, "log": str(log), "error": error, "resources": resources, "warnings": len(re.findall(rb"^warning: (?!.*generated \d+ warning)", result.stderr, re.M))})
        if returncode and label == "build":
            raise RuntimeError(f"The {label} check failed. Read {log}.")
    binary, = (candidate,) if candidate is not None else sorted({
        item["executable"] for line in result.stdout.splitlines()
        if line.startswith(b"{") and (item := json.loads(line)).get("executable")
        and "bin" in item["target"]["kind"]
    })
    return Path(binary), {
        "commands": commands, "rust_tests": sum(map(int, re.findall(rb"test result: ok\. (\d+) passed", (logs / "test.log").read_bytes()))),
        "pedantic_warnings": next(item["warnings"] for item in commands if "-W" in item["command"]),
        "unsafe_uses": sum(len(re.findall(r"\bunsafe\b", path.read_text(errors="replace"))) for path in (project / "implementation/src").rglob("*.rs")),
    }


def candidate_failures(reference, candidate, pin):
    linked = subprocess.run(["otool", "-L", str(candidate)], capture_output=True, text=True, check=bool(pin.get("forbidden_libraries"))).stdout
    return (["The candidate is not a runnable regular file."] if not candidate.is_file() or not os.access(candidate, os.X_OK) else []) + [f"The candidate links the forbidden library {name}." for name in pin.get("forbidden_libraries", []) if f"/{name}.framework/" in linked or f"/lib{name}." in linked] + (["The candidate contains the reference path, so it can run the original."] if str(reference).encode() in candidate.read_bytes() else [])


def run(track, pin, score):
    parser = argparse.ArgumentParser(description=f"Score a {track} reconstruction against the pinned reference.")
    parser.add_argument("--project", type=Path, default=REPOSITORY / "work/projects" / track)
    parser.add_argument("--output", type=Path, default=REPOSITORY / "work/evaluation" / track)
    parser.add_argument("--frozen", action="store_true", help="Score the executable from the frozen comparison report.")
    args = parser.parse_args()
    project, output = args.project.resolve(), project_helper.work_root(args.project.resolve(), args.output.resolve()) if args.frozen else args.output.resolve()
    report = {"track": track, "project": str(project), "status": "failed"}
    try:
        executable = reference(track, pin)
        report["reference_sha256"] = pin["sha256"]
        if not (project / "implementation/Cargo.toml").is_file():
            raise ValueError(f"The project is missing. Reconstruct {executable} into {project}.")
        identity = yaml.safe_load((project / "verification/comparison.yaml").read_text())["executables"] if args.frozen else None
        candidate = project_helper.artifact(project, (project / identity["candidate"]["path"]).relative_to(project).as_posix(), False) if args.frozen else None
        if args.frozen and (identity["reference"]["sha256"] != pin["sha256"] or digest(candidate.read_bytes()) != identity["candidate"]["sha256"] or candidate_failures(executable, candidate, pin)):
            raise ValueError("The frozen executable identity or eligibility check failed.")
        binaries = (candidate, executable) if args.frozen else ()
        report["freeze"] = freeze(project, binaries=binaries)
        try:
            report["checkpoints"] = project_helper.status(project)
        except (OSError, ValueError, KeyError) as error:
            report["checkpoints"] = {"error": str(error)}
        candidate, report["rust"] = rust(project, output / "logs", candidate)
        report["candidate_sha256"] = digest(candidate.read_bytes())
        failures = [f"The {item['command'][1]} check failed. Read {item['log']}." for item in report["rust"].get("commands", []) if item["returncode"]] + candidate_failures(executable, candidate, pin)
        if args.frozen and freeze(project, binaries=binaries) != report["freeze"]:
            raise ValueError("The frozen project or executable changed during the quality checks.")
        reports, score_failures = score(executable, candidate, project)
        if args.frozen and freeze(project, binaries=binaries) != report["freeze"]:
            raise ValueError("The frozen project or executable changed during scoring.")
        for name, value in reports.items():
            value["cases"] = [case if not case.get("passed", True) else {"id": case.get("id", case.get("input", {}).get("id")), "passed": True} for case in value.get("cases", [])]
            save(output / f"{name}.yaml", value)
        report["reports"] = {name: {key: value[key] for key in ("status", "passed", "failed")} for name, value in reports.items()}
        report["witnesses"] = {name: [{"id": identity, "feature": identity.split("/")[0], "differences": case.get("differences", case.get("failures")), "report": str(output / f"{name}.yaml")} for case in value.get("cases", []) if not case.get("passed", True) and "execution_error" not in (case.get("differences") or []) and (identity := case.get("id", case.get("input", {}).get("id")))] for name, value in reports.items() if name != "repeatability"}
        report["failures"] = failures + score_failures
        reference_error = any(value["status"] == "invalid" for value in reports.values()) or any(isinstance(case.get("reference"), dict) and case["reference"].get("error") for value in reports.values() for case in value.get("cases", []))
        report["status"] = "invalid" if reference_error or reports.get("repeatability", {"status": "passed"})["status"] != "passed" else "passed" if reports and all(value["status"] == "passed" for value in reports.values()) and not report["failures"] else "failed"
    except (OSError, ValueError, KeyError, TypeError, RuntimeError, yaml.YAMLError, subprocess.SubprocessError) as error:
        report["error"] = str(error)
    save(output / "report.yaml", report)
    print(yaml.safe_dump({key: value for key, value in report.items() if key != "freeze"}, sort_keys=False), end="")
    return 0 if report["status"] == "passed" else 1
