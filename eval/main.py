#!/usr/bin/env python3
"""Run the current Rustify skills with an agent on blind tasks and grade each trial."""

import argparse
from pathlib import Path

import yaml

import agent


HERE = Path(__file__).resolve().parent
DEFAULT = ("base64", "b3sum", "xh")


def task(value):
    runner = next(HERE.glob(f"*/{value}/run.py"), Path(value) / "run.py")
    if not runner.is_file():
        raise argparse.ArgumentTypeError(f"{value} is not a task name or a task folder.")
    return runner.parent.resolve()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tasks", nargs="*", type=task, metavar="TASK", help="A task name or a private task folder. The default is base64, b3sum, and xh.")
    parser.add_argument("--trials", type=int, default=3)
    args = parser.parse_args()
    stamp = agent.run(args.tasks or [task(name) for name in DEFAULT], args.trials)
    report = agent.grade(stamp)
    print(yaml.safe_dump(report["summary"], sort_keys=False) + f"The grades are in {stamp / 'grades.yaml'}.")
    return 0 if all(item["level"] == "target" for item in report["summary"].values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
