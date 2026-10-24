"""Check branch protection and preservation of existing hooks."""

import importlib.util
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("install_hooks", ROOT / "scripts/install_hooks.py")
installer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(installer)


class PushGuardTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        (self.root / ".githooks").mkdir()
        shutil.copy2(ROOT / ".githooks/pre-push", self.root / ".githooks/pre-push")
        self.previous = self.root / "previous-hooks"
        self.previous.mkdir()
        (self.previous / "pre-commit").write_text("#!/bin/sh\nexit 0\n")
        hook = self.previous / "pre-push"
        hook.write_text(f"#!{sys.executable}\nimport sys\nfrom pathlib import Path\nPath({str(self.root / 'captured')!r}).write_bytes(sys.stdin.buffer.read())\n")
        hook.chmod(0o755)
        subprocess.run(["git", "-C", str(self.root), "config", "--local", "core.hooksPath", str(self.previous)], check=True)
        installer.ROOT = self.root
        installer.main()
        self.hook = self.root / ".git/rustify-hooks/pre-push"

    def push(self, branch):
        data = f"refs/heads/work {'a' * 40} refs/heads/{branch} {'b' * 40}\n".encode()
        result = subprocess.run([str(self.hook), "origin", "unused"], input=data, capture_output=True)
        return result, data

    def test_main_is_blocked_before_existing_hook_runs(self):
        result, _ = self.push("main")
        self.assertEqual(result.returncode, 1)
        self.assertFalse((self.root / "captured").exists())

    def test_feature_push_preserves_existing_hook_input(self):
        result, data = self.push("feature")
        self.assertEqual(result.returncode, 0)
        self.assertEqual((self.root / "captured").read_bytes(), data)
        self.assertEqual((self.hook.parent / "pre-commit").resolve(), self.previous / "pre-commit")

    def test_repeated_install_keeps_the_existing_chain(self):
        installer.main()
        result, data = self.push("feature")
        self.assertEqual(result.returncode, 0)
        self.assertEqual((self.root / "captured").read_bytes(), data)


if __name__ == "__main__":
    unittest.main()
