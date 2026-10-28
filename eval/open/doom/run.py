#!/usr/bin/env python3
"""Score a doomgeneric reconstruction against the pinned hardened reference."""

from pathlib import Path
import sys
import tempfile

import yaml

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(next(path for path in ROOT.parents if (path / "harness.py").is_file())))
import harness
from cases import generate, milestones, upstream
import runner

PIN = yaml.safe_load((ROOT / "reference.yaml").read_text())
MANUAL = [
    {"feature": "renderer", "reason": "The engine draws frames only to the SDL window. The in-engine screenshot needs a live key event, and the host denies screen capture and synthetic input to the scorer."},
    {"feature": "menus", "reason": "Menus need live keyboard input. Key timing against game tics is not reproducible without synthetic input."},
    {"feature": "status-bar", "reason": "The status bar and the HUD appear only in frames."},
    {"feature": "automap", "reason": "The automap needs a key press and appears only in frames."},
    {"feature": "cheats", "reason": "Cheats need typed keys. Demos cannot carry them."},
    {"feature": "controls", "reason": "Keyboard play needs live input."},
    {"feature": "window", "reason": "The window title and the scaled frame need screen capture."},
    {"feature": "screenshot", "reason": "The screenshot key is unbound by default, and the build does not read configuration files."},
]


def score(reference, candidate, project):
    for name, expected in PIN.get("resource_sha256", {}).items():
        if harness.digest((reference.parent / name).read_bytes()) != expected:
            raise ValueError(f"The resource hash differs from the pin: {name}")
    wad = runner.Wad(reference.parent / "freedoom1.wad")
    groups = {**milestones(), "generate-demos": generate(), **upstream(wad)}
    reports = {"repeatability": runner.compare(reference, reference, wad, [case for cases in groups.values() for case in cases])}
    reports.update({name: runner.compare(reference, candidate, wad, cases) for name, cases in groups.items()})
    reports["replay-complete"]["manual"] = MANUAL
    failures = [f"The {item['feature']} check has no verified manual evidence. {item['reason']}" for item in MANUAL]
    with tempfile.TemporaryDirectory() as directory:
        for label, body in (("wrong-output", 'printf "Doom\\n"'), ("wrong-version", f'exec "{reference}" "$@" -gameversion final')):
            wrong = Path(directory) / label
            wrong.write_text(f"#!/bin/sh\n{body}\n")
            wrong.chmod(0o755)
            if runner.compare(reference, wrong, wad, groups["replay-core"][:1] + groups["replay-core"][3:4])["status"] != "failed":
                failures.append(f"The {label} control passes.")
    return reports, failures


if __name__ == "__main__":
    raise SystemExit(harness.run("doom", PIN, score))
