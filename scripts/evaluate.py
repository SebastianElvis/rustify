#!/usr/bin/env python3
"""Score agent-generated projects against the compact binary reconstruction dataset."""

import argparse
from pathlib import Path
import subprocess
import sys
import time

import yaml


ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--track", choices=("base64", "b3sum", "xh", "zenity"), action="append")
    parser.add_argument("--desktop", action="store_true", help="Also score the zenity track from saved GUI captures.")
    parser.add_argument("--projects", type=Path, default=ROOT / "work/projects")
    args = parser.parse_args()
    tracks = list(dict.fromkeys(args.track or ["base64", "b3sum", "xh"]))
    if args.desktop and "zenity" not in tracks:
        tracks.append("zenity")
    start = time.monotonic()
    results = []
    for track in tracks:
        runner = next((ROOT / "evaluations").glob(f"*/{track}/run.py"))
        result = subprocess.run([sys.executable, str(runner), "--project", str(args.projects.resolve() / track)], cwd=ROOT)
        results.append({"track": track, "returncode": result.returncode})
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


if __name__ == "__main__":
    raise SystemExit(main())
