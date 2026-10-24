#!/usr/bin/env python3
"""Keep reconstruction checkpoints and detect stale evidence."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import tempfile


PHASES = ("prepare", "discover", "plan", "implement", "validate")
REQUIRED = {
    "prepare": ("recovered/contract.json",),
    "discover": ("recovered/product.md", "recovered/ux.md", "recovered/architecture.md", "recovered/evidence.json", "recovered/scenarios.json", "recovered/tests.json", "recovered/roadmap.md"),
    "plan": ("rust-design.md", "plan.json"),
    "implement": ("implementation/Cargo.toml", "implementation/Cargo.lock", "verification/checks.json"),
    "validate": ("verification/comparison.json", "verification/compatibility.md"),
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
    if check_content and path.suffix == ".json":
        value = json.loads(path.read_text())
        if not isinstance(value, (list, dict)) or not value:
            raise ValueError(f"The JSON artifact must have content: {name}")
    return path


def save(root, state):
    directory = root / "recovered"
    if directory.is_symlink() or (directory / "state.json").is_symlink():
        raise ValueError("The state cannot use a symlink.")
    directory.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="w", dir=directory, delete=False) as stream:
        name = stream.name
        json.dump(state, stream, indent=2)
        stream.write("\n")
    try:
        os.replace(name, directory / "state.json")
    finally:
        Path(name).unlink(missing_ok=True)


def init(project, target, profile, work_dir=None):
    root = project_root(project)
    workspace = work_root(root, work_dir if work_dir is not None else root.parent / ("." + root.name + "-rustify"))
    if (root / "recovered/state.json").exists() or (root / "recovered").is_symlink() or (root / "recovered/state.json").is_symlink():
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
    state = {"version": 2, "profile": profile, "target": {"path": str(binary.resolve()), "sha256": digest(binary)}, "work_dir": str(workspace), "checkpoints": {}}
    save(root, state)
    return state


def load(root):
    state = json.loads(artifact(root, "recovered/state.json").read_text())
    if state["version"] != 2 or not Path(state["work_dir"]).is_absolute():
        raise ValueError("The project state must use version 2 and an absolute agent workspace.")
    work_root(root, state["work_dir"])
    target = Path(state["target"]["path"])
    if target.is_symlink() or not target.is_file() or digest(target) != state["target"]["sha256"]:
        raise ValueError("The target changed. Start a new project for the new target.")
    return state


def files_for(root, phase, state):
    names = set(REQUIRED[phase])
    base = work_root(root, state["work_dir"]) if phase == "plan" else root
    hashes = {name: digest(artifact(base, name)) for name in sorted(names)}
    if phase in {"implement", "discover"}:
        tree = root / ("implementation" if phase == "implement" else "recovered/evidence")
        for directory, folders, files in os.walk(tree):
            if phase == "implement":
                folders[:] = [name for name in folders if name != ".git" and (Path(directory) != tree or name != "target")]
            if Path(directory).is_symlink() or any((Path(directory) / name).is_symlink() for name in folders):
                raise ValueError("An input directory cannot be a symlink.")
            for name in files:
                path = Path(directory) / name
                if path.is_symlink() or not path.is_file():
                    raise ValueError("Inputs must use regular files without symlinks.")
                hashes[path.relative_to(root).as_posix()] = digest(path)
    if phase == "implement":
        if not any(name.endswith(".rs") for name in hashes):
            raise ValueError("The implementation must contain Rust source.")
        checks = json.loads((root / "verification/checks.json").read_text())
        latest = {}
        for record in checks.get("commands", []):
            command = record.get("command", record.get("args", []))
            if len(command) >= 2 and command[0] == "cargo":
                latest[command[1]] = record.get("returncode")
        if checks.get("status") != "passed" or any(latest.get(name) != 0 for name in ("fmt", "clippy", "test")):
            raise ValueError("The latest format, clippy, and test checks must pass.")
    if phase == "validate":
        contract = json.loads((root / "recovered/contract.json").read_text())
        if all(isinstance(contract.get(key), dict) for key in ("compatibility", "scope")) and contract["compatibility"].get("mode") == "faithful" and contract["scope"].get("mode") == "full_product":
            path = artifact(root, "verification/parity.json")
            parity = json.loads(path.read_text())
            if parity.get("status") != "passed" or parity.get("full_parity_gate_pass") is not True or parity.get("errors") != [] or parity.get("gaps") != [] or parity.get("target_sha256") != state["target"]["sha256"]:
                raise ValueError("The full-product parity evidence gate must pass.")
            inputs = parity.get("inputs", {})
            if not inputs or any(digest(artifact(root, name, False)) != value for name, value in inputs.items()):
                raise ValueError("The parity evidence changed after the gate.")
            hashes["verification/parity.json"] = digest(path)
        report = json.loads((root / "verification/comparison.json").read_text())
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


def freshness(root, state):
    completed = []
    stale = None
    for phase in PHASES:
        expected = state["checkpoints"].get(phase)
        if expected is None:
            break
        try:
            current = files_for(root, phase, state)
        except (OSError, ValueError, KeyError, TypeError):
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
    record = commands.add_parser("checkpoint")
    record.add_argument("project")
    record.add_argument("phase", choices=PHASES)
    args = parser.parse_args()
    try:
        if args.command == "init":
            result = init(args.project, args.target, args.profile, args.work_dir)
        elif args.command == "status":
            result = status(args.project)
        else:
            result = checkpoint(args.project, args.phase)
        print(json.dumps(result, indent=2))
        return 0
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(1, f"{error}\n")


if __name__ == "__main__":
    raise SystemExit(main())
