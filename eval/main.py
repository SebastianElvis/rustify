#!/usr/bin/env python3
"""Evaluate Rustify reconstructions and the Rustify skills on the pinned tracks."""

import argparse
from pathlib import Path
import subprocess
import sys
import time

import yaml

import agent
import build
import distinguish


ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / "eval"
DEFAULT = ("base64", "b3sum", "xh")


def score(args):
    tracks = list(dict.fromkeys(args.track or DEFAULT))
    if args.desktop and "zenity" not in tracks:
        tracks.append("zenity")
    start = time.monotonic()
    results = []
    for track in tracks:
        runner = next(HERE.glob(f"*/{track}/run.py"))
        result = subprocess.run([sys.executable, str(runner), "--project", str(args.projects.resolve() / track)], cwd=ROOT)
        saved = ROOT / "work/evaluation" / track / "report.yaml"
        scored = (yaml.safe_load(saved.read_text()).get("scores") or {}) if saved.is_file() else {}
        results.append({"track": track, "returncode": result.returncode, **{name: scored.get(name) for name in ("fps", "cpr", "milestone_credit")}})
    report = {
        "status": "passed" if all(item["returncode"] == 0 for item in results) else "failed",
        "tracks": results,
        "seconds": round(time.monotonic() - start, 2),
    }
    destination = ROOT / "work/evaluation/summary.yaml"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(yaml.safe_dump(report, sort_keys=False))
    print(yaml.safe_dump(report, sort_keys=False), end="")
    return 0 if report["status"] == "passed" else 1


def references(args):
    for track in args.tracks:
        report = build.build(track)
        print(yaml.safe_dump({key: report[key] for key in ("track", "binary", "binary_sha256", "audit")}, sort_keys=False), end="")
    return 0


def trials(args):
    if args.action == "run":
        stamp = agent.run([path.resolve() for path in args.track or [HERE / "open" / name for name in DEFAULT]], args.agent, args.trials, args.output.resolve(), args.timeout)
    else:
        stamp = args.run.resolve()
    if args.action == "resume":
        agent.resume(stamp, args.agent, args.timeout)
    if getattr(args, "no_grade", False):
        print(stamp)
        return 0
    report = agent.grade(stamp)
    print(yaml.safe_dump(report["summary"], sort_keys=False), end="")
    return 0 if all(item["level"] == "target" for item in report["summary"].values()) else 1


def game(args):
    summary = distinguish.play(args.reference, args.candidate, args.agent, args.budget, args.name, args.output.resolve(), args.timeout, args.seed)
    print(yaml.safe_dump({key: value for key, value in summary.items() if key not in {"witness_cases", "inconclusive_cases", "replays"}}, sort_keys=False), end="")
    return 0 if summary["status"] == "passed" else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    scores = commands.add_parser("score", help="Score the agent projects in work/projects with the track scorers.")
    scores.add_argument("--track", choices=sorted(path.parent.name for path in HERE.glob("*/*/run.py")), action="append")
    scores.add_argument("--desktop", action="store_true", help="Also score the zenity track from saved GUI captures.")
    scores.add_argument("--projects", type=Path, default=ROOT / "work/projects")
    scores.set_defaults(func=score)
    builds = commands.add_parser("build", help="Build hardened reference binaries from the pinned recipes.")
    builds.add_argument("tracks", nargs="+")
    builds.set_defaults(func=references)
    actions = commands.add_parser("agent", help="Run the current skills with an agent on blind tracks and grade each trial.").add_subparsers(dest="action", required=True)
    start = actions.add_parser("run")
    start.add_argument("--agent", required=True, help="The agent command. The harness sends the prompt on standard input.")
    start.add_argument("--track", action="append", type=Path, help="A track folder with run.py and grading.yaml. Private tracks can live outside the repository.")
    start.add_argument("--trials", type=int, default=3)
    start.add_argument("--output", type=Path, default=ROOT / "work/agent-eval")
    start.add_argument("--timeout", type=float, default=4 * 3600)
    start.add_argument("--no-grade", action="store_true")
    actions.add_parser("grade").add_argument("run", type=Path)
    again = actions.add_parser("resume", help="Resume trials that stopped on an agent error, then grade.")
    again.add_argument("run", type=Path)
    again.add_argument("--agent", required=True, help="The agent command. The harness appends --resume and the session.")
    again.add_argument("--timeout", type=float, default=4 * 3600)
    again.add_argument("--no-grade", action="store_true")
    for action in actions.choices.values():
        action.set_defaults(func=trials)
    play = commands.add_parser("distinguish", help="Run the adaptive distinguisher game between an original program and its reconstruction.")
    play.add_argument("--reference", required=True)
    play.add_argument("--candidate", required=True)
    play.add_argument("--agent", required=True, help="The agent command. The harness sends the prompt on standard input.")
    play.add_argument("--name", required=True, help="The argument-zero name of both programs.")
    play.add_argument("--budget", type=int, default=200)
    play.add_argument("--timeout", type=float, default=10)
    play.add_argument("--seed", type=int, default=None)
    play.add_argument("--output", type=Path, required=True)
    play.set_defaults(func=game)
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
