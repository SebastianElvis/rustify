#!/usr/bin/env python3
"""Run the current Rustify skills with an agent on blind targets and grade each trial."""

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
import time


ROOT = Path(__file__).resolve().parents[1]
PROMPT = """Use the rustify skill to reconstruct {binary} in Rust.
Write the target project to {project}.
The contract scope is {scope}.
Work only from the binary, its resources, and its observable behavior.
Do not download, search for, or read the source code, tests, or documentation of this program.
Complete every phase, run the parity gate, and report the remaining gaps.
"""


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


compare = load("compare", ROOT / "skills/rustify-validate/scripts/compare.py")
parity = load("parity", ROOT / "skills/rustify-validate/scripts/parity.py")
project_helper = load("project", ROOT / "skills/rustify/scripts/project.py")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n")


def targets(manifest):
    base = manifest.parent
    result = []
    for target in json.loads(manifest.read_text())["targets"]:
        binary = (base / target["binary"]).resolve()
        if not binary.is_file() and target.get("setup"):
            subprocess.run(target["setup"], cwd=ROOT, check=True)
        if not binary.is_file() or sha(binary) != target["sha256"]:
            raise ValueError(f"The binary for {target['id']} is missing or differs from its pinned hash.")
        grading = target["grading"]
        result.append({**target, "binary": binary, "grading": {**grading, "vectors": (base / grading["vectors"]).resolve()}})
    return result


def freeze(directory):
    return {path.relative_to(directory).as_posix(): sha(path) for path in sorted(directory.rglob("*")) if path.is_file() and path.relative_to(directory).parts[:2] != ("implementation", "target")}


def run(manifest, agent, trials, output, timeout):
    stamp = output / time.strftime("%Y%m%d-%H%M%S")
    selected = targets(manifest)
    save(stamp / "targets.json", {"targets": [{**item, "binary": str(item["binary"]), "grading": {**item["grading"], "vectors": str(item["grading"]["vectors"])}} for item in selected]})
    for target in selected:
        for trial in range(1, trials + 1):
            workspace = stamp / target["id"] / f"trial-{trial}"
            for folder in (".claude/skills", ".agents/skills"):
                shutil.copytree(ROOT / "skills", workspace / folder)
            binary = workspace / "input" / target["name"]
            binary.parent.mkdir(parents=True)
            shutil.copy2(target["binary"], binary)
            prompt = PROMPT.format(binary=binary, project=workspace / "project", scope=target["scope"])
            start = time.monotonic()
            try:
                process = subprocess.run(shlex.split(agent), cwd=workspace, input=prompt, capture_output=True, text=True, timeout=timeout)
                returncode, stdout, stderr = process.returncode, process.stdout, process.stderr
            except subprocess.TimeoutExpired as error:
                returncode, stdout, stderr = None, error.stdout or "", "The agent exceeded the time limit."
            seconds = round(time.monotonic() - start, 1)
            (workspace / "agent.log").write_text(stdout + stderr)
            record = {"target": target["id"], "trial": trial, "agent": agent, "returncode": returncode, "seconds": seconds}
            try:
                usage = json.loads(stdout)
                record.update(usage=usage.get("usage"), cost_usd=usage.get("total_cost_usd"))
            except (json.JSONDecodeError, AttributeError):
                pass
            project = workspace / "project"
            record["freeze"] = freeze(project) if project.is_dir() else {}
            save(workspace / "run.json", record)
    return stamp


def candidate(project, build):
    implementation = project / "implementation"
    result = subprocess.run(["cargo", "build", "--release", "--locked", "--message-format=json"], cwd=implementation, env={**os.environ, "CARGO_TARGET_DIR": str(build)}, capture_output=True, text=True)
    executables = [message["executable"] for message in map(json.loads, result.stdout.splitlines()) if message.get("reason") == "compiler-artifact" and message.get("executable") and "bin" in message["target"]["kind"]]
    if result.returncode or len(executables) != 1:
        raise ValueError("The release build must produce exactly one executable.")
    return Path(executables[0])


def recall(patterns, text):
    found = [item["id"] for item in patterns if re.search(item["pattern"], text)]
    return {"found": len(found), "total": len(patterns), "rate": round(len(found) / len(patterns), 3) if patterns else None, "missing": sorted({item["id"] for item in patterns} - set(found))}


def text(project, documents, key, fields):
    parts = [(project / name).read_text(errors="replace") for name in documents if (project / name).is_file()]
    try:
        model = json.loads((project / "recovered/model.json").read_text())
        parts += [str(item.get(field, "")) for item in model.get(key, []) for field in fields]
    except (OSError, json.JSONDecodeError, AttributeError):
        pass
    return "\n".join(parts)


def grade_trial(workspace, target):
    record = json.loads((workspace / "run.json").read_text())
    project = workspace / "project"
    result = {"target": target["id"], "trial": record["trial"], "seconds": record["seconds"], "cost_usd": record.get("cost_usd"), "agent_returncode": record["returncode"]}
    if not project.is_dir() or freeze(project) != record["freeze"]:
        return {**result, "success": False, "error": "The project is missing or changed after the freeze."}
    product = text(project, ("recovered/product.md", "recovered/ux.md"), "requirements", ("statement",))
    architecture = text(project, ("recovered/architecture.md",), "components", ("name", "responsibility"))
    result["product_recall"] = recall(target["grading"]["features"], product)
    result["architecture_recall"] = recall(target["grading"]["components"], architecture)
    gate = parity.check(project)
    structure = gate.get("reflexion")
    result["parity"] = {"assessment": gate["assessment"], "errors": gate["errors"], "gaps": len(gate["gaps"])}
    result["structural_fidelity"] = result["edge_convergence"] = None
    if structure:
        model = json.loads((project / "recovered/model.json").read_text())
        merged = sum(item["rust"] in structure["merged"] for item in model["correspondences"])
        components = len(model["components"])
        edges = len(structure["convergences"]) + len(structure["absences"])
        result["structural_fidelity"] = round((components - len(structure["unmapped"]) - merged) / components, 3) if components else None
        result["edge_convergence"] = round(len(structure["convergences"]) / edges, 3) if edges else None
    try:
        result["checkpoints"] = project_helper.status(project)["completed"]
    except (OSError, ValueError, KeyError, TypeError) as error:
        result["checkpoints"] = f"unavailable: {error}"
    checks = project / "verification/checks.json"
    mutation = [item["mutation"] for item in json.loads(checks.read_text()).get("commands", []) if "mutation" in item] if checks.is_file() else []
    result["mutation_score"] = mutation[-1]["score"] if mutation else None
    try:
        executable = candidate(project, workspace / "build")
        vectors = json.loads(target["grading"]["vectors"].read_text())
        report = compare.compare(target["binary"], executable, vectors["cases"], name=target["name"])
        valid = passed = 0
        for case in report["cases"]:
            expected = vectors["expected"][case["input"]["id"]]
            if case["reference"]["error"] is None and all(case["reference"][key] == value for key, value in expected.items()):
                valid += 1
                passed += case["candidate"]["error"] is None and all(case["candidate"][key] == value for key, value in expected.items())
        result["blind_vectors"] = {"passed": passed, "valid": valid, "total": len(report["cases"]), "rate": round(passed / valid, 3) if valid else None}
        lint = subprocess.run(["cargo", "clippy", "--release", "--locked", "--", "-W", "clippy::pedantic"], cwd=project / "implementation", env={**os.environ, "CARGO_TARGET_DIR": str(workspace / "build")}, capture_output=True, text=True)
        result["pedantic_warnings"] = len(re.findall(r"^warning: (?!.*generated \d+ warning)", lint.stderr, re.M))
        result["unsafe_blocks"] = sum(len(re.findall(r"\bunsafe\b", path.read_text(errors="replace"))) for path in (project / "implementation/src").rglob("*.rs"))
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        result["error"] = str(error)
    result["success"] = result.get("blind_vectors", {}).get("rate") == 1.0
    return result


def grade(stamp):
    manifest = stamp / "targets.json"
    rows, summary = [], {}
    for target in targets(manifest):
        trials = [grade_trial(path, target) for path in sorted((stamp / target["id"]).glob("trial-*"))]
        rows += trials
        rates = [item["blind_vectors"]["rate"] for item in trials if item.get("blind_vectors", {}).get("rate") is not None]
        summary[target["id"]] = {
            "trials": len(trials), "pass_at_k": any(item["success"] for item in trials), "pass_hat_k": bool(trials) and all(item["success"] for item in trials),
            "mean_blind_rate": round(sum(rates) / len(rates), 3) if rates else None,
            "mean_seconds": round(sum(item["seconds"] for item in trials) / len(trials), 1) if trials else None,
        }
    report = {"summary": summary, "trials": rows}
    save(stamp / "grades.json", report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    start = commands.add_parser("run")
    start.add_argument("--targets", type=Path, required=True)
    start.add_argument("--agent", required=True)
    start.add_argument("--trials", type=int, default=3)
    start.add_argument("--output", type=Path, default=ROOT / "work/agent-eval")
    start.add_argument("--timeout", type=float, default=4 * 3600)
    start.add_argument("--no-grade", action="store_true")
    score = commands.add_parser("grade")
    score.add_argument("run", type=Path)
    args = parser.parse_args()
    stamp = args.run if args.command == "grade" else run(args.targets.resolve(), args.agent, args.trials, args.output.resolve(), args.timeout)
    if args.command == "run" and args.no_grade:
        print(stamp)
        return 0
    report = grade(stamp)
    print(json.dumps(report["summary"], indent=2))
    return 0 if all(item["pass_hat_k"] for item in report["summary"].values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
