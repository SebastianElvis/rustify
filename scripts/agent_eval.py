#!/usr/bin/env python3
"""Run the current Rustify skills with an agent on blind tracks and grade each trial."""

import argparse
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import sys
import time

import yaml


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "evaluations"))
import harness

load, save, freeze = harness.load, harness.save, harness.freeze
PROMPT = """Use the rustify skill to reconstruct {binary} in Rust.
Write the target project to {project}.
Create an open replacement for the complete product.
The reconstruction must not invoke the original executable or reuse its closed feature libraries.
Generic operating system services remain available.
Work only from the binary, its resources, and its observable behavior.
Do not download, search for, or read the source code, tests, or documentation of this program.
Complete every phase, run the parity gate, and report the remaining gaps.
"""
RESUME = "Continue the reconstruction from where you stopped. Follow the same rules. Complete every phase, run the parity gate, and report the remaining gaps.\n"


def reference(directory):
    sys.path.insert(0, str(directory))
    recipe = directory / "reference.yaml"
    pin = yaml.safe_load(recipe.read_text()) if recipe.is_file() else load(f"track_{directory.name}", directory / "run.py").PIN
    return harness.reference(directory.name, pin), pin


def run(directories, agent, trials, output, timeout):
    stamp = output / time.strftime("%Y%m%d-%H%M%S")
    save(stamp / "tracks.yaml", [str(directory) for directory in directories])
    for directory in directories:
        source, pin = reference(directory)
        for trial in range(1, trials + 1):
            workspace = stamp / directory.name / f"trial-{trial}"
            for folder in (".claude/skills", ".agents/skills"):
                shutil.copytree(ROOT / "skills", workspace / folder)
            binary = workspace / "input" / directory.name if source.is_relative_to(ROOT) else source
            if binary != source:
                binary.parent.mkdir(parents=True)
                shutil.copy2(source, binary)
                for name in pin.get("resources", {}):
                    shutil.copyfile(source.parent / name, binary.parent / name)
            prompt = PROMPT.format(binary=binary, project=workspace / "project")
            if pin.get("forbidden_libraries"):
                prompt += "The reconstruction must not link these libraries: " + ", ".join(pin["forbidden_libraries"]) + ".\n"
            attempt(workspace, {"track": directory.name, "trial": trial, "seconds": 0, "cost_usd": 0, "skills": {name: freeze(workspace / name, ("__pycache__",)) for name in (".agents/skills", ".claude/skills")}}, shlex.split(agent), prompt, timeout)
    return stamp


def attempt(workspace, record, command, prompt, timeout):
    """The helper records one attempt and freezes its project."""
    start = time.monotonic()
    process, error, resources = harness.compare.execute(command, cwd=workspace, stdin=prompt.encode(), env={**os.environ, "CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS": "0"}, timeout=timeout, memory_mib=2048, process_limit=32, output_mib=16)
    stdout, stderr = process.stdout.decode(errors="replace"), process.stderr.decode(errors="replace") + (error or "")
    record.update(agent=shlex.join(command), returncode=None if error else process.returncode, seconds=round(record["seconds"] + time.monotonic() - start, 1), error="agent_failed" if error or process.returncode != 0 else None, execution_error=error, resources=resources)
    with (workspace / "agent.log").open("a") as log:
        log.write(stdout + stderr + "\n")
    try:
        usage = json.loads(stdout)
        record.update(usage=usage.get("usage"), cost_usd=round((record.get("cost_usd") or 0) + (usage.get("total_cost_usd") or 0), 4), session=usage.get("session_id") or record.get("session"), error=(usage.get("api_error") or "agent_failed") if usage.get("is_error") else record["error"])
    except (json.JSONDecodeError, AttributeError):
        pass
    project = workspace / "project"
    record["freeze"] = freeze(project) if project.is_dir() else {}
    save(workspace / "run.yaml", record)


def resume(stamp, agent, timeout):
    """The helper resumes saved sessions after agent errors or failed parity reports."""
    for workspace in sorted(stamp.glob("*/trial-*")):
        record, parity = yaml.safe_load((workspace / "run.yaml").read_text()), workspace / "project/verification/parity.yaml"
        if (record.get("error") or (parity.is_file() and (yaml.safe_load(parity.read_text()) or {}).get("full_parity_gate_pass") is not True)) and record.get("session"):
            if (workspace / "score").exists():
                raise ValueError("A scored trial needs a new blind run.")
            attempt(workspace, record, [*shlex.split(agent), "--resume", record["session"]], RESUME, timeout)


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
    skills = record.get("skills")
    if skills is not None and any(freeze(workspace / name, ("__pycache__",)) != hashes for name, hashes in skills.items()):
        return {**result, "error": "The installed skills changed during the trial."}
    result["skills_verified"] = skills is not None
    output = workspace / "score" / str(time.time_ns())
    _, error, result["scorer_resources"] = harness.compare.execute([sys.executable, str(directory / "run.py"), "--project", str(project), "--output", str(output), "--frozen"], timeout=3600, memory_mib=2048, process_limit=32, output_mib=16)
    if error or not (output / "report.yaml").is_file():
        return {**result, "error": error or "The scorer did not write its report."}
    score = yaml.safe_load((output / "report.yaml").read_text())
    reports = [value for name, value in score.get("reports", {}).items() if name not in {"repeatability", "parsers-format", "parse-outputs"}]
    total = sum(value["passed"] + value["failed"] for value in reports)
    result.update(score_report=str(output / "report.yaml"), success=score["status"] == "passed", scorer_status=score["status"], scorer_error=score.get("error"), expected_failures=len(score.get("failures", [])))
    result["blind_pass_rate"] = round(sum(value["passed"] for value in reports) / total, 3) if total and score["status"] != "invalid" else None
    result["product_recall"] = recall(grading["features"], text(project, ("recovered/product.md", "recovered/ux.md"), "requirements", ("statement",)))
    result["architecture_recall"] = recall(grading["components"], text(project, ("recovered/architecture.md",), "components", ("name", "responsibility")))
    gate_path = (workspace / ".agents/skills" if skills is not None else ROOT / "skills") / "rustify-validate/scripts/parity.py"
    gate = load("trial_parity", gate_path).check(project)
    result["success"] = result["success"] and gate["full_parity_gate_pass"] and score.get("checkpoints", {}).get("completed") == ["discover", "plan", "implement", "validate"]
    result["parity"] = {"assessment": gate["assessment"], "errors": gate["errors"], "gaps": len(gate["gaps"]), "helper_sha256": harness.digest(gate_path)}
    result["structural_fidelity"] = result["edge_convergence"] = None
    if structure := gate.get("reflexion"):
        model = yaml.safe_load((project / "recovered/model.yaml").read_text())
        merged = sum(item["rust"] in structure["merged"] for item in model["correspondences"])
        components, edges = len(model["components"]), len(structure["convergences"]) + len(structure["absences"])
        result["structural_fidelity"] = round((components - len(structure["unmapped"]) - merged) / components, 3) if components else None
        result["edge_convergence"] = round(len(structure["convergences"]) / edges, 3) if edges else None
    checks = project / "verification/checks.yaml"
    mutation = [item["mutation"] for item in yaml.safe_load(checks.read_text()).get("commands", []) if "mutation" in item] if checks.is_file() else []
    result["mutation_score"] = mutation[-1]["score"] if mutation else None
    result.update({name: score.get("rust", {}).get(name) for name in ("pedantic_warnings", "unsafe_uses")})
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
    again = commands.add_parser("resume", help="Resume trials that stopped on an agent error, then grade.")
    again.add_argument("run", type=Path)
    again.add_argument("--agent", required=True, help="The agent command. The harness appends --resume and the session.")
    again.add_argument("--timeout", type=float, default=4 * 3600)
    again.add_argument("--no-grade", action="store_true")
    args = parser.parse_args()
    if args.command == "grade":
        stamp = args.run.resolve()
    elif args.command == "resume":
        stamp = args.run.resolve()
        resume(stamp, args.agent, args.timeout)
    else:
        tracks = [path.resolve() for path in args.track or [ROOT / "evaluations/open" / name for name in ("base64", "b3sum", "xh")]]
        stamp = run(tracks, args.agent, args.trials, args.output.resolve(), args.timeout)
    if getattr(args, "no_grade", False):
        print(stamp)
        return 0
    report = grade(stamp)
    print(yaml.safe_dump(report["summary"], sort_keys=False), end="")
    return 0 if all(item["pass_hat_k"] for item in report["summary"].values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
