#!/usr/bin/env python3
"""Run the current Rustify skills with an agent on blind tracks and grade each trial."""

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

import yaml


ROOT = Path(__file__).resolve().parents[1]
PROMPT = """Use the rustify skill to reconstruct {binary} in Rust.
Write the target project to {project}.
Reconstruct the complete product.
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


sys.path.insert(0, str(ROOT / "evaluations"))
harness = load("harness", ROOT / "evaluations/harness.py")
parity = load("rustify_parity", ROOT / "skills/rustify-validate/scripts/parity.py")


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(value, sort_keys=False))


def freeze(project):
    return {path.relative_to(project).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(project.rglob("*")) if path.is_file() and path.relative_to(project).parts[:2] != ("implementation", "target")}


def reference(directory):
    sys.path.insert(0, str(directory))
    track = load(f"track_{directory.name}", directory / "run.py")
    return harness.reference(directory.name, track.PIN)


def run(directories, agent, trials, output, timeout):
    stamp = output / time.strftime("%Y%m%d-%H%M%S")
    save(stamp / "tracks.yaml", [str(directory) for directory in directories])
    for directory in directories:
        source = reference(directory)
        for trial in range(1, trials + 1):
            workspace = stamp / directory.name / f"trial-{trial}"
            for folder in (".claude/skills", ".agents/skills"):
                shutil.copytree(ROOT / "skills", workspace / folder)
            binary = workspace / "input" / directory.name
            binary.parent.mkdir(parents=True)
            shutil.copy2(source, binary)
            prompt = PROMPT.format(binary=binary, project=workspace / "project")
            start = time.monotonic()
            try:
                process = subprocess.run(shlex.split(agent), cwd=workspace, input=prompt, capture_output=True, text=True, timeout=timeout)
                returncode, stdout, stderr = process.returncode, process.stdout, process.stderr
            except subprocess.TimeoutExpired as error:
                returncode, stdout, stderr = None, error.stdout or "", "The agent exceeded the time limit."
            record = {"track": directory.name, "trial": trial, "agent": agent, "returncode": returncode, "seconds": round(time.monotonic() - start, 1)}
            (workspace / "agent.log").write_text(stdout + stderr)
            try:
                usage = json.loads(stdout)
                record.update(usage=usage.get("usage"), cost_usd=usage.get("total_cost_usd"))
            except (json.JSONDecodeError, AttributeError):
                pass
            project = workspace / "project"
            record["freeze"] = freeze(project) if project.is_dir() else {}
            save(workspace / "run.yaml", record)
    return stamp


def recall(patterns, text):
    found = {item["id"] for item in patterns if re.search(item["pattern"], text)}
    return {"rate": round(len(found) / len(patterns), 3) if patterns else None, "missing": sorted({item["id"] for item in patterns} - found)}


def text(project, documents, key, fields):
    parts = [(project / name).read_text(errors="replace") for name in documents if (project / name).is_file()]
    try:
        parts += [str(item.get(field, "")) for item in yaml.safe_load((project / "recovered/model.yaml").read_text()).get(key, []) for field in fields]
    except (OSError, yaml.YAMLError, AttributeError):
        pass
    return "\n".join(parts)


def grade_trial(workspace, directory, grading):
    record = yaml.safe_load((workspace / "run.yaml").read_text())
    project = workspace / "project"
    result = {"track": directory.name, "trial": record["trial"], "seconds": record["seconds"], "cost_usd": record.get("cost_usd"), "agent_returncode": record["returncode"], "success": False}
    if not project.is_dir() or freeze(project) != record["freeze"]:
        return {**result, "error": "The project is missing or changed after the freeze."}
    subprocess.run([sys.executable, str(directory / "run.py"), "--project", str(project), "--output", str(workspace / "score")], capture_output=True)
    score = yaml.safe_load((workspace / "score/report.yaml").read_text())
    reports = [value for name, value in score.get("reports", {}).items() if name != "repeatability"]
    total = sum(value["passed"] + value["failed"] for value in reports)
    result.update(success=score["status"] == "passed", scorer_error=score.get("error"), expected_failures=len(score.get("failures", [])))
    result["blind_pass_rate"] = round(sum(value["passed"] for value in reports) / total, 3) if total else None
    result["product_recall"] = recall(grading["features"], text(project, ("recovered/product.md", "recovered/ux.md"), "requirements", ("statement",)))
    result["architecture_recall"] = recall(grading["components"], text(project, ("recovered/architecture.md",), "components", ("name", "responsibility")))
    gate = parity.check(project)
    structure = gate.get("reflexion")
    result["parity"] = {"assessment": gate["assessment"], "errors": gate["errors"], "gaps": len(gate["gaps"])}
    result["structural_fidelity"] = result["edge_convergence"] = None
    if structure:
        model = yaml.safe_load((project / "recovered/model.yaml").read_text())
        merged = sum(item["rust"] in structure["merged"] for item in model["correspondences"])
        components, edges = len(model["components"]), len(structure["convergences"]) + len(structure["absences"])
        result["structural_fidelity"] = round((components - len(structure["unmapped"]) - merged) / components, 3) if components else None
        result["edge_convergence"] = round(len(structure["convergences"]) / edges, 3) if edges else None
    checks = project / "verification/checks.yaml"
    mutation = [item["mutation"] for item in yaml.safe_load(checks.read_text()).get("commands", []) if "mutation" in item] if checks.is_file() else []
    result["mutation_score"] = mutation[-1]["score"] if mutation else None
    if (project / "implementation/Cargo.toml").is_file():
        lint = subprocess.run(["cargo", "clippy", "--locked", "--", "-W", "clippy::pedantic"], cwd=project / "implementation", env={**os.environ, "CARGO_TARGET_DIR": str(workspace / "build")}, capture_output=True, text=True)
        result["pedantic_warnings"] = len(re.findall(r"^warning: (?!.*generated \d+ warning)", lint.stderr, re.M))
        result["unsafe_uses"] = sum(len(re.findall(r"\bunsafe\b", path.read_text(errors="replace"))) for path in (project / "implementation/src").rglob("*.rs"))
    return result


def grade(stamp):
    rows, summary = [], {}
    for directory in map(Path, yaml.safe_load((stamp / "tracks.yaml").read_text())):
        grading = yaml.safe_load((directory / "grading.yaml").read_text())
        trials = [grade_trial(path, directory, grading) for path in sorted((stamp / directory.name).glob("trial-*"))]
        rows += trials
        rates = [item["blind_pass_rate"] for item in trials if item.get("blind_pass_rate") is not None]
        summary[directory.name] = {
            "trials": len(trials), "pass_at_k": any(item["success"] for item in trials), "pass_hat_k": bool(trials) and all(item["success"] for item in trials),
            "mean_blind_pass_rate": round(sum(rates) / len(rates), 3) if rates else None,
            "mean_seconds": round(sum(item["seconds"] for item in trials) / len(trials), 1) if trials else None,
        }
    report = {"summary": summary, "trials": rows}
    save(stamp / "grades.yaml", report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    start = commands.add_parser("run")
    start.add_argument("--agent", required=True, help="The agent command. The harness sends the prompt on standard input.")
    start.add_argument("--track", action="append", type=Path, help="A track folder with run.py and grading.yaml. Private tracks can live outside the repository.")
    start.add_argument("--trials", type=int, default=3)
    start.add_argument("--output", type=Path, default=ROOT / "work/agent-eval")
    start.add_argument("--timeout", type=float, default=4 * 3600)
    start.add_argument("--no-grade", action="store_true")
    commands.add_parser("grade").add_argument("run", type=Path)
    args = parser.parse_args()
    if args.command == "grade":
        stamp = args.run.resolve()
    else:
        tracks = [path.resolve() for path in args.track or [ROOT / "evaluations/open" / name for name in ("base64", "b3sum", "xh")]]
        stamp = run(tracks, args.agent, args.trials, args.output.resolve(), args.timeout)
        if args.no_grade:
            print(stamp)
            return 0
    report = grade(stamp)
    print(yaml.safe_dump(report["summary"], sort_keys=False), end="")
    return 0 if all(item["pass_hat_k"] for item in report["summary"].values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
