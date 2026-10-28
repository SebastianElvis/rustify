"""Run the current Rustify skills with an agent on blind tracks and grade each trial."""

import json
import os
from pathlib import Path
import re
import shlex
import shutil
import statistics
import sys
import time

import yaml


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "eval"))
import harness

load, save, freeze = harness.load, harness.save, harness.freeze
PROMPT = """/rustify {binary} {project}
Create an open replacement for the complete product.
The reconstruction must not invoke the original executable or reuse its closed feature libraries.
Generic operating system services remain available.
Work only from the binary, its resources, and its observable behavior.
Do not download, search for, or read the source code, tests, or documentation of this program.
Complete every phase, run the parity gate, and report the remaining gaps.
"""
# The tier targets come from published whole-program results. eval/docs/benchmark.md records the evidence.
TARGETS = {"small": (0.95, 0.90), "medium": (0.85, 0.75), "large": (0.70, 0.55)}
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
            prompt = PROMPT.format(binary=shlex.quote(str(binary)), project=shlex.quote(str(workspace / "project")))
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
    result.update(score_report=str(output / "report.yaml"), success=score["status"] == "passed", scorer_status=score["status"], scorer_error=score.get("error"), expected_failures=len(score.get("failures", [])))
    result.update({name: score.get("scores", {}).get(name) for name in ("gate", "cpr", "fps", "coverage", "milestones", "milestone_credit")})
    try:
        own = yaml.safe_load((project / "verification/comparison.yaml").read_text())
        result["self_check_gap"] = round(own["passed"] / (own["passed"] + own["failed"]) - result["cpr"], 3)
    except (OSError, yaml.YAMLError, KeyError, TypeError, ZeroDivisionError):
        result["self_check_gap"] = None
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
        fps, cpr = ([item.get(name) or 0 for item in trials] for name in ("fps", "cpr"))
        target, floor = TARGETS.get(grading.get("tier"), (None, None))
        median = round(statistics.median(fps), 3) if fps else None
        summary[directory.name] = {
            "trials": len(trials), "pass_at_k": any(item["success"] for item in trials), "pass_hat_k": bool(trials) and all(item["success"] for item in trials),
            "tier": grading.get("tier"), "fps_median": median, "fps_stderr": round(statistics.stdev(fps) / len(fps) ** 0.5, 3) if len(fps) > 1 else None,
            "cpr_median": round(statistics.median(cpr), 3) if cpr else None, "fps_target": target, "fps_floor": floor,
            "level": None if target is None or median is None else "target" if median >= target else "floor" if median >= floor else "below",
            "mean_seconds": round(sum(item["seconds"] for item in trials) / len(trials), 1) if trials else None,
        }
    report = {"summary": summary, "trials": rows}
    save(stamp / "grades.yaml", report)
    return report
