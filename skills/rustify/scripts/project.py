#!/usr/bin/env python3
"""Keep reconstruction checkpoints and detect stale evidence."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time

import yaml


PHASES = ("discover", "plan", "implement", "validate")
REQUIRED = {
    "discover": ("recovered/product.md", "recovered/ux.md", "recovered/architecture.md", "recovered/evidence.yaml", "recovered/scenarios.yaml", "recovered/tests.yaml", "recovered/roadmap.md", "recovered/model.yaml#inventory,requirements,components,edges"),
    "plan": ("recovered/model.yaml#correspondences,slices", "implementation/docs/design.md"),
    "implement": ("implementation/Cargo.toml", "implementation/Cargo.lock", "verification/checks.yaml"),
    "validate": ("verification/comparison.yaml", "verification/parity.yaml", "verification/compatibility.md"),
}
CHECKS = {
    "fmt": ["cargo", "fmt", "--check"],
    "clippy": ["cargo", "clippy", "--locked", "--all-targets", "--", "-D", "warnings"],
    "test": ["cargo", "test", "--locked"],
    "deny": ["cargo", "deny", "check"],
    "mutants": ["cargo", "mutants", "--output"],
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def project_root(project):
    path = Path(project).absolute()
    if path.is_symlink():
        raise ValueError("The project cannot be a symlink.")
    return path.resolve()


def work_root(root, value):
    path = Path(value).absolute()
    if any(parent.is_symlink() for parent in (path, *path.parents)):
        raise ValueError("The agent workspace cannot use a symlink.")
    path = path.resolve()
    if path == root or root in path.parents:
        raise ValueError("The agent workspace must stay outside the project.")
    return path


def artifact(root, name, check_content=True):
    relative = Path(name)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("An artifact must stay inside its directory.")
    path = root / relative
    for parent in (path, *path.parents):
        if parent == root:
            break
        if parent.is_symlink():
            raise ValueError("An artifact cannot use a symlink.")
    if not path.is_file() or (check_content and not path.read_bytes().strip()):
        raise ValueError(f"The artifact is missing or empty: {name}")
    if check_content and path.suffix == ".yaml":
        value = yaml.safe_load(path.read_text())
        if not isinstance(value, (list, dict)) or not value:
            raise ValueError(f"The YAML artifact must have content: {name}")
    return path


def section(root, name):
    path, _, keys = name.partition("#")
    if not keys:
        return digest(artifact(root, path))
    value = yaml.safe_load(artifact(root, path).read_text())
    keys = keys.split(",")
    if not isinstance(value, dict) or any(value.get(key) is None for key in keys):
        raise ValueError(f"The artifact lacks a required section: {name}")
    return hashlib.sha256(yaml.safe_dump({key: value[key] for key in keys}).encode()).hexdigest()


def tree(root, name):
    hashes = {}
    base = root / name
    for directory, folders, files in os.walk(base):
        if name == "implementation":
            folders[:] = [folder for folder in folders if folder != ".git" and (Path(directory) != base or folder != "target")]
        if Path(directory).is_symlink() or any((Path(directory) / folder).is_symlink() for folder in folders):
            raise ValueError("An input directory cannot be a symlink.")
        for filename in files:
            path = Path(directory) / filename
            if path.is_symlink() or not path.is_file():
                raise ValueError("Inputs must use regular files without symlinks.")
            hashes[path.relative_to(root).as_posix()] = digest(path)
    return hashes


def combined(hashes):
    return hashlib.sha256(yaml.safe_dump(hashes).encode()).hexdigest()


def check_plan(model):
    requirements = {item["id"]: item for item in model["requirements"]}
    components = {item["id"] for item in model["components"]}
    slices = {item["id"]: item for item in model["slices"]}
    if not slices or len(slices) != len(model["slices"]):
        raise ValueError("The plan needs slices with unique identifiers.")
    skeletons = [item for item in slices.values() if item["kind"] == "skeleton"]
    if len(skeletons) != 1 or skeletons[0]["depends_on"]:
        raise ValueError("The plan needs one walking skeleton without predecessors.")
    for item in slices.values():
        if item["kind"] not in {"skeleton", "slice"} or item["risk"] not in {"high", "medium", "low"} or not item["requirements"]:
            raise ValueError(f"The slice has an invalid kind, risk, or requirement list: {item['id']}")
        if set(item["requirements"]) - set(requirements) or set(item["depends_on"]) - set(slices) or (item["kind"] == "slice" and not item["depends_on"]):
            raise ValueError(f"The slice has an invalid reference: {item['id']}")
    ordered, pending = set(), dict(slices)
    while pending:
        ready = [identity for identity, item in pending.items() if set(item["depends_on"]) <= ordered]
        if not ready:
            raise ValueError("The slice dependencies contain a cycle.")
        ordered.update(ready)
        for identity in ready:
            del pending[identity]
    planned = {identity for item in slices.values() for identity in item["requirements"]}
    if set(requirements) - planned:
        raise ValueError("Every requirement needs a slice.")
    if any(item["original"] not in components for item in model["correspondences"]):
        raise ValueError("A correspondence names an unknown original component.")


def save(root, state):
    directory = root / "recovered"
    if directory.is_symlink() or (directory / "state.yaml").is_symlink():
        raise ValueError("The state cannot use a symlink.")
    directory.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="w", dir=directory, delete=False) as stream:
        name = stream.name
        yaml.safe_dump(state, stream, sort_keys=False)
    try:
        os.replace(name, directory / "state.yaml")
    finally:
        Path(name).unlink(missing_ok=True)


def init(project, target, profile, work_dir=None):
    root = project_root(project)
    workspace = work_root(root, work_dir if work_dir is not None else root.parent / ("." + root.name + "-rustify"))
    if (root / "recovered/state.yaml").exists() or (root / "recovered").is_symlink() or (root / "recovered/state.yaml").is_symlink():
        raise ValueError("The project already has state.")
    binary = Path(target).absolute()
    if binary.is_symlink() or not binary.is_file():
        raise ValueError("The target must be a regular file without a symlink.")
    for name in ("recovered/evidence", "implementation", "verification/logs"):
        path = root / name
        if path.is_symlink() or any(parent.is_symlink() for parent in path.parents if parent != root):
            raise ValueError("A project directory cannot use a symlink.")
        path.mkdir(parents=True, exist_ok=True)
    workspace.mkdir(parents=True, exist_ok=True)
    state = {"version": 3, "profile": profile, "target": {"path": str(binary.resolve()), "sha256": digest(binary)}, "work_dir": str(workspace), "checkpoints": {}}
    save(root, state)
    return state


def load(root):
    state = yaml.safe_load(artifact(root, "recovered/state.yaml").read_text())
    if state["version"] != 3 or not Path(state["work_dir"]).is_absolute():
        raise ValueError("The project state must use version 3 and an absolute agent workspace.")
    work_root(root, state["work_dir"])
    target = Path(state["target"]["path"])
    if target.is_symlink() or not target.is_file() or digest(target) != state["target"]["sha256"]:
        raise ValueError("The target changed. Start a new project for the new target.")
    return state


def files_for(root, phase, state):
    hashes = {name: section(root, name) for name in REQUIRED[phase]}
    if phase == "discover":
        hashes.update(tree(root, "recovered/evidence"))
    if phase == "plan":
        check_plan(yaml.safe_load((root / "recovered/model.yaml").read_text()))
    if phase == "implement":
        inputs = tree(root, "implementation")
        if not any(name.endswith(".rs") for name in inputs):
            raise ValueError("The implementation must contain Rust source.")
        hashes.update(inputs)
        checks = yaml.safe_load((root / "verification/checks.yaml").read_text())
        latest = {record.get("name"): record for record in checks.get("commands", [])}
        if checks.get("status") != "passed" or checks.get("inputs_sha256") != combined(inputs) or any(latest.get(name, {}).get("returncode") != 0 for name in ("fmt", "clippy", "test")):
            raise ValueError("The latest format, clippy, and test checks must pass for the current implementation.")
        if any(digest(artifact(root, record["log"], False)) != record["log_sha256"] for record in latest.values()):
            raise ValueError("A check log differs from its record.")
    if phase == "validate":
        parity = yaml.safe_load((root / "verification/parity.yaml").read_text())
        if parity.get("assessment") != "full_parity_pass" or parity.get("errors") != [] or parity.get("target_sha256") != state["target"]["sha256"] or parity.get("gaps") != []:
            raise ValueError("The parity gate must report full_parity_pass.")
        inputs = parity.get("inputs", {})
        if not inputs or any(digest(artifact(root, name, False)) != value for name, value in inputs.items()):
            raise ValueError("The parity evidence changed after the gate.")
        report = yaml.safe_load((root / "verification/comparison.yaml").read_text())
        cases = report.get("cases", [])
        if report.get("status") != "passed" or report.get("failed") != 0 or not cases or report.get("passed") != len(cases):
            raise ValueError("The comparison must pass every recorded case.")
        if any(case.get("passed") is not True or case.get("differences") != [] for case in cases):
            raise ValueError("The comparison must pass at least one case.")
        if report["executables"]["reference"]["sha256"] != state["target"]["sha256"]:
            raise ValueError("The comparison uses a different target.")
        candidate = report["executables"]["candidate"]
        name = Path(candidate["path"]).relative_to(root).as_posix()
        hashes[name] = digest(artifact(root, name))
        if hashes[name] != candidate["sha256"]:
            raise ValueError("The candidate changed after the comparison.")
    return hashes


def check(project, extra=()):
    root = project_root(project)
    load(root)
    path = root / "verification/checks.yaml"
    records = yaml.safe_load(path.read_text()).get("commands", []) if path.is_file() else []
    inputs = tree(root, "implementation")
    status = "passed"
    for name in ("fmt", "clippy", "test", *extra):
        stamp = f"{name}-{time.time_ns()}"
        log = root / "verification/logs" / f"{stamp}.log"
        command = CHECKS[name] + ([str(log.with_suffix(""))] if name == "mutants" else [])
        log.parent.mkdir(parents=True, exist_ok=True)
        with log.open("wb") as stream:
            returncode = subprocess.run(command, cwd=root / "implementation", stdout=stream, stderr=subprocess.STDOUT).returncode
        record = {"name": name, "command": command, "returncode": returncode, "log": log.relative_to(root).as_posix(), "log_sha256": digest(log)}
        if name == "mutants":
            outcomes = log.with_suffix("") / "mutants.out/outcomes.json"
            counts = json.loads(outcomes.read_text()) if outcomes.is_file() else {}
            record["mutation"] = {key: counts.get(key) for key in ("caught", "missed", "timeout", "unviable")}
            tested = sum(counts.get(key, 0) for key in ("caught", "missed", "timeout"))
            record["mutation"]["score"] = counts["caught"] / tested if tested else None
        elif returncode:
            status = "failed"
        records.append(record)
    if tree(root, "implementation") != inputs:
        status = "failed"
    path.write_text(yaml.safe_dump({"status": status, "inputs_sha256": combined(inputs), "commands": records}, sort_keys=False))
    return {"status": status, "commands": [{key: record[key] for key in ("name", "returncode")} for record in records[-len(extra) - 3:]]}


def freshness(root, state):
    completed = []
    stale = None
    for phase in PHASES:
        expected = state["checkpoints"].get(phase)
        if expected is None:
            break
        try:
            current = files_for(root, phase, state)
        except (OSError, ValueError, KeyError, TypeError, yaml.YAMLError):
            current = None
        if current != expected:
            stale = phase
            break
        completed.append(phase)
    return {"completed": completed, "next": PHASES[len(completed)] if len(completed) < len(PHASES) else None, "stale": stale}


def status(project):
    root = project_root(project)
    return freshness(root, load(root))


def checkpoint(project, phase):
    root = project_root(project)
    state = load(root)
    progress = freshness(root, state)
    if phase != progress["next"]:
        raise ValueError(f"The next phase is {progress['next']}.")
    hashes = files_for(root, phase, state)
    state["checkpoints"] = {name: state["checkpoints"][name] for name in progress["completed"]}
    state["checkpoints"][phase] = hashes
    save(root, state)
    return freshness(root, state)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    create = commands.add_parser("init")
    create.add_argument("project")
    create.add_argument("--target", required=True)
    create.add_argument("--profile", choices=("cli", "desktop", "service", "game"), default="cli")
    create.add_argument("--work-dir")
    commands.add_parser("status").add_argument("project")
    verify = commands.add_parser("check")
    verify.add_argument("project")
    verify.add_argument("--deny", action="store_true")
    verify.add_argument("--mutants", action="store_true")
    record = commands.add_parser("checkpoint")
    record.add_argument("project")
    record.add_argument("phase", choices=PHASES)
    args = parser.parse_args()
    try:
        if args.command == "init":
            result = init(args.project, args.target, args.profile, args.work_dir)
        elif args.command == "status":
            result = status(args.project)
        elif args.command == "check":
            result = check(args.project, [name for name in ("deny", "mutants") if getattr(args, name)])
        else:
            result = checkpoint(args.project, args.phase)
        print(yaml.safe_dump(result, sort_keys=False), end="")
        return 0
    except (OSError, ValueError, KeyError, TypeError, yaml.YAMLError) as error:
        parser.exit(1, f"{error}\n")


if __name__ == "__main__":
    raise SystemExit(main())
