#!/usr/bin/env python3
"""Fetch and verify the pinned evaluation binary."""

import hashlib
import json
from pathlib import Path
import platform
import subprocess
import tarfile


ROOT = Path(__file__).resolve().parents[1]


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def fetch(url):
    return subprocess.check_output(["curl", "-fsSL", "--retry", "2", "--max-time", "120", url])


def main():
    if platform.system() != "Darwin" or platform.machine() != "arm64":
        raise SystemExit("This reference binary requires macOS arm64.")
    manifest = json.loads((ROOT / "evaluations/base64/target/recovered/provenance.json").read_text())
    directory = ROOT / "work/downloads"
    directory.mkdir(parents=True, exist_ok=True)
    binary = directory / "base64"
    if binary.exists() and sha256(binary.read_bytes()) == manifest["binary_sha256"]:
        print(binary)
        return
    token = json.loads(fetch("https://ghcr.io/token?service=ghcr.io&scope=repository:homebrew/core/coreutils:pull"))["token"]
    request = f'header = "Authorization: Bearer {token}"\n'
    data = subprocess.check_output(["curl", "-fsSL", "--retry", "2", "--max-time", "120", "--config", "-", manifest["bottle_url"]], input=request.encode())
    if sha256(data) != manifest["bottle_sha256"]:
        raise SystemExit("The reference archive hash does not match.")
    archive = directory / "coreutils.tar.gz"
    archive.write_bytes(data)
    with tarfile.open(archive) as stream:
        member = stream.getmember(manifest["binary_member"])
        if not member.isfile():
            raise SystemExit("The reference member is not a regular file.")
        data = stream.extractfile(member).read()
    if sha256(data) != manifest["binary_sha256"]:
        raise SystemExit("The reference binary hash does not match.")
    binary.write_bytes(data)
    binary.chmod(0o755)
    print(binary)


if __name__ == "__main__":
    main()
