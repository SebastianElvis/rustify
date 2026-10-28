#!/usr/bin/env python3
"""Check real Skills CLI and Claude Code plugin installations in a temporary project."""

import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

import yaml


ROOT = Path(__file__).resolve().parents[1]


def main():
    with tempfile.TemporaryDirectory(prefix="rustify-install-") as temporary:
        directory = Path(temporary)
        subprocess.run(
            ["npx", "--yes", "skills@1.7.4", "add", str(ROOT), "--skill", "*", "--agent", "codex", "--yes"],
            cwd=directory, env={**os.environ, "DISABLE_TELEMETRY": "1"}, check=True,
        )
        installed = directory / ".agents/skills"
        expected = {path.name for path in (ROOT / "skills").iterdir() if (path / "SKILL.md").is_file()}
        actual = {path.name for path in installed.iterdir() if (path / "SKILL.md").is_file()}
        if actual != expected or len(actual) != 8:
            raise RuntimeError("The installer did not discover the eight skills.")
        detached = directory / "detached"
        shutil.copytree(installed, detached, symlinks=False)
        helper = detached / "rustify/scripts/project.py"
        project = directory / "target-project"
        subprocess.run([sys.executable, str(helper), "init", str(project), "--target", str(Path(sys.executable).resolve())], check=True)
        cases = directory / "cases.yaml"
        cases.write_text(yaml.safe_dump([{"id": "installed-helper", "args": []}]))
        subprocess.run([sys.executable, str(detached / "rustify-probe/scripts/compare.py"), "--reference", "/usr/bin/true", "--candidate", "/usr/bin/true", "--cases", str(cases), "--report", str(directory / "report.yaml"), "--name", "true"], check=True)
        subprocess.run([sys.executable, str(detached / "rustify-probe/scripts/fuzz.py"), "--reference", "/usr/bin/true", "--candidate", "/usr/bin/true", "--seeds", str(cases), "--report", str(directory / "fuzz.yaml"), "--iterations", "3"], check=True)
        result = subprocess.run([sys.executable, str(detached / "rustify-validate/scripts/parity.py"), "--project", str(project), "--report", str(directory / "parity.yaml")], capture_output=True)
        parity = yaml.safe_load((directory / "parity.yaml").read_text())
        if result.returncode != 1 or parity["status"] != "failed" or not parity["errors"]:
            raise RuntimeError("The installed parity gate did not reject missing evidence.")
        print("The installer copied all eight skills. All four detached helpers pass.")
        if shutil.which("claude"):
            claude = {**os.environ, "CLAUDE_CONFIG_DIR": str(directory / "claude")}
            for command in (["validate", str(ROOT)], ["marketplace", "add", str(ROOT)], ["install", "rustify@rustify"]):
                subprocess.run(["claude", "plugin", *command], env=claude, check=True)
            if "Skills (8)" not in subprocess.check_output(["claude", "plugin", "details", "rustify@rustify"], env=claude, text=True):
                raise RuntimeError("The Claude Code plugin does not contain the eight skills.")
            print("The Claude Code plugin installs all eight skills.")


if __name__ == "__main__":
    main()
