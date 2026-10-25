#!/usr/bin/env python3
"""Score a GNU base64 reconstruction against the pinned reference."""

from pathlib import Path
import sys

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import harness
from challenge_cases import cases

ROOT = Path(__file__).resolve().parent
PIN = {
    "url": "https://ghcr.io/v2/homebrew/core/coreutils/blobs/sha256:c845a8ad8933ec45614e331e4f861862a4766a716ea7c13ee102e50a056c7792",
    "token_url": "https://ghcr.io/token?service=ghcr.io&scope=repository:homebrew/core/coreutils:pull",
    "archive_sha256": "c845a8ad8933ec45614e331e4f861862a4766a716ea7c13ee102e50a056c7792",
    "member": "coreutils/9.12_1/bin/gbase64",
    "sha256": "41dd92cf260491c5c8fc0084c42e58b1baaca9ebcc88aa38f60a17a2ef603570",
}


def score(reference, candidate, project):
    challenge = cases()
    upstream = yaml.safe_load((ROOT / "upstream-vectors.yaml").read_text())
    runs = (("repeatability", challenge + upstream["cases"], reference), ("challenge", challenge, candidate), ("upstream", upstream["cases"], candidate))
    reports = {name: harness.compare.compare(reference, executable, items, name="base64") for name, items, executable in runs}
    failures = [f"{case['input']['id']}/{side}" for case in reports["upstream"]["cases"] for side in ("reference", "candidate") if case[side]["error"] or any(case[side][key] != value for key, value in upstream["expected"][case["input"]["id"]].items())]
    return reports, failures


if __name__ == "__main__":
    raise SystemExit(harness.run("base64", PIN, score))
