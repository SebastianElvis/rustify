#!/usr/bin/env python3
"""Run the compact binary reconstruction dataset."""

import argparse
import json
from pathlib import Path
import subprocess
import sys
import time


ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--track", choices=("base64", "b3sum", "xh"), action="append")
    parser.add_argument("--recorded-desktop", action="store_true")
    args = parser.parse_args()
    tracks = list(dict.fromkeys(args.track or ["base64", "b3sum", "xh"]))
    if args.recorded_desktop:
        tracks.append("zenity")
    start = time.monotonic()
    results = []
    for track in tracks:
        runner = ROOT / "evaluations" / track / "run.py"
        result = subprocess.run([sys.executable, str(runner)], cwd=ROOT)
        results.append({"track": track, "returncode": result.returncode})
    report = {
        "status": "passed" if all(item["returncode"] == 0 for item in results) else "failed",
        "tracks": results,
        "seconds": round(time.monotonic() - start, 2),
        "live_gui_replay": False,
    }
    destination = ROOT / "work/evaluation/summary.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
