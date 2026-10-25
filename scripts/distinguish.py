#!/usr/bin/env python3
"""Run the adaptive distinguisher game between an original program and its reconstruction."""

import argparse
import importlib.util
import os
from pathlib import Path
import random
import shlex
import subprocess
import sys

import yaml


ROOT = Path(__file__).resolve().parents[1]
PROMPT = """You play a distinguishing game. Two command-line programs hide behind the labels A and B.
One label is an original program. The other label is a reconstruction that tries to behave identically.
Your goal is to find probes on which A and B give different views.

Run `{python} probe.py LABEL CASE_FILE` to execute one probe. LABEL is A or B.
CASE_FILE is a YAML mapping with `id`, `args` (a list of strings), and optional `stdin_b64`, `files` (relative path to base64 content), and `env`.
The tool prints the view: return code, standard output, standard error, and the files after the run.
You have {budget} probe runs in total. Each run on A or B counts as one.
The program name (argument zero) is `{name}`. Start with `--help`, `--version`, and invalid options, then target edge cases, rare options, malformed inputs, large inputs, and option combinations.

Do not read, copy, disassemble, or inspect the executables or the file `{config}`. Use only probe.py.
When you stop, write `witnesses.yaml`: a YAML list of the cases that you believe distinguish A from B.
"""
PROBE = """import os, sys, yaml
sys.path.insert(0, {compare_dir!r})
from compare import run, validate
config = yaml.safe_load(open(os.environ["DISTINGUISH_CONFIG"]))
log = config["log"]
used = sum(1 for _ in open(log)) if os.path.exists(log) else 0
if used >= config["budget"]:
    sys.exit("The probe budget is spent.")
label, case = sys.argv[1], yaml.safe_load(open(sys.argv[2]))
validate([case])
view = run(config["programs"][label], config["name"], case, config["timeout"])
with open(log, "a") as stream:
    stream.write(yaml.safe_dump({{"label": label, "case": case}}, default_flow_style=True, width=1 << 30))
print(yaml.safe_dump(view, sort_keys=False))
"""


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def play(reference, candidate, agent, budget, name, output, timeout, seed):
    compare = load("rustify_compare", ROOT / "skills/rustify-validate/scripts/compare.py")
    labels = ["A", "B"]
    random.Random(seed).shuffle(labels)
    secret = {labels[0]: str(Path(reference).resolve()), labels[1]: str(Path(candidate).resolve())}
    workspace, config = output / "workspace", output / "config.yaml"
    workspace.mkdir(parents=True, exist_ok=True)
    config.write_text(yaml.safe_dump({"programs": secret, "name": name, "budget": budget, "timeout": timeout, "log": str(output / "probes.log")}))
    (workspace / "probe.py").write_text(PROBE.format(compare_dir=str(ROOT / "skills/rustify-validate/scripts")))
    prompt = PROMPT.format(python=sys.executable, budget=budget, name=name, config=config)
    environment = {**os.environ, "DISTINGUISH_CONFIG": str(config)}
    result = subprocess.run(shlex.split(agent), cwd=workspace, input=prompt, env=environment, capture_output=True, text=True, timeout=4 * 3600)
    (output / "agent.log").write_text(result.stdout + result.stderr)
    probes = [yaml.safe_load(line) for line in (output / "probes.log").read_text().splitlines()] if (output / "probes.log").exists() else []
    claimed = yaml.safe_load((workspace / "witnesses.yaml").read_text()) if (workspace / "witnesses.yaml").exists() else []
    key = lambda case: yaml.safe_dump({name: value for name, value in case.items() if name != "id"}, sort_keys=True)
    first, cases = {}, {}
    for index, case in enumerate([item["case"] for item in probes] + (claimed or [])):
        first.setdefault(key(case), index + 1 if index < len(probes) else None)
        cases.setdefault(key(case), {**case, "id": f"probe-{len(cases) + 1}"})
    report = compare.compare(reference, candidate, list(cases.values()), timeout, name) if cases else {"cases": []}
    witnesses = [row["input"] for row in report["cases"] if not row["passed"]]
    found = [first[key(case)] for case in witnesses if first[key(case)]]
    summary = {
        "class": "D-adaptive", "labels": {labels[0]: "original", labels[1]: "candidate"},
        "budget": budget, "probes": len(probes), "replayed_cases": len(cases), "witnesses": len(witnesses),
        "query_complexity": min(found) if found else None, "path_leak": any(path in result.stdout for path in secret.values()),
        "status": "passed" if not witnesses else "failed", "witness_cases": witnesses,
    }
    (output / "report.yaml").write_text(yaml.safe_dump(summary, sort_keys=False))
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference", required=True)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--agent", required=True, help="The agent command. The harness sends the prompt on standard input.")
    parser.add_argument("--name", required=True, help="The argument-zero name of both programs.")
    parser.add_argument("--budget", type=int, default=200)
    parser.add_argument("--timeout", type=float, default=10)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    summary = play(args.reference, args.candidate, args.agent, args.budget, args.name, args.output.resolve(), args.timeout, args.seed)
    print(yaml.safe_dump({key: value for key, value in summary.items() if key != "witness_cases"}, sort_keys=False), end="")
    return 0 if summary["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
