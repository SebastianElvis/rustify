"""Test the agent evaluation harness with a scripted agent."""

import base64
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("agent_eval", ROOT / "scripts/agent_eval.py")
agent_eval = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(agent_eval)

AGENT = '''import re, sys
from pathlib import Path
project = Path(re.search(r"Write the target project to (.+)\\.", sys.stdin.read()).group(1))
files = {
    "recovered/product.md": "REQ-1: The upper program shall write uppercase bytes.\\n",
    "recovered/architecture.md": "C-1 is the entry component.\\n",
    "implementation/Cargo.toml": "[package]\\nname = \\"upper\\"\\nversion = \\"0.1.0\\"\\nedition = \\"2021\\"\\n",
    "implementation/Cargo.lock": "version = 3\\n\\n[[package]]\\nname = \\"upper\\"\\nversion = \\"0.1.0\\"\\n",
    "implementation/src/main.rs": "use std::io::{Read, Write};\\nfn main() {\\n    let mut data = Vec::new();\\n    std::io::stdin().read_to_end(&mut data).unwrap();\\n    std::io::stdout().write_all(&data.to_ascii_uppercase()).unwrap();\\n}\\n",
}
for name, text in files.items():
    (project / name).parent.mkdir(parents=True, exist_ok=True)
    (project / name).write_text(text)
'''


def encoded(value):
    return base64.b64encode(value).decode("ascii")


@unittest.skipUnless(shutil.which("cargo"), "The harness test needs cargo.")
class AgentEvaluationTests(unittest.TestCase):
    def test_scripted_agent_trials_are_frozen_and_graded(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            reference = root / "upper"
            reference.write_text("#!" + sys.executable + "\nimport sys\nsys.stdout.buffer.write(sys.stdin.buffer.read().upper())\n")
            reference.chmod(0o755)
            (root / "agent.py").write_text(AGENT)
            (root / "vectors.json").write_text(json.dumps({"cases": [{"id": "v1", "args": [], "stdin_b64": encoded(b"ab")}], "expected": {"v1": {"returncode": 0, "stdout_b64": encoded(b"AB"), "stderr_b64": ""}}}))
            manifest = root / "targets.json"
            manifest.write_text(json.dumps({"targets": [{
                "id": "upper", "name": "upper", "binary": "upper", "sha256": hashlib.sha256(reference.read_bytes()).hexdigest(), "scope": "the full product",
                "grading": {"vectors": "vectors.json", "features": [{"id": "uppercase", "pattern": "(?i)uppercase"}, {"id": "help", "pattern": "--help"}], "components": [{"id": "entry", "pattern": "(?i)entry"}]},
            }]}))
            stamp = agent_eval.run(manifest, f"{sys.executable} {root / 'agent.py'}", 2, root / "out", 120)
            self.assertTrue((stamp / "upper/trial-1/.claude/skills/rustify/SKILL.md").is_file())
            report = agent_eval.grade(stamp)
            self.assertEqual(report["summary"]["upper"]["pass_hat_k"], True)
            trial = report["trials"][0]
            self.assertEqual(trial["blind_vectors"], {"passed": 1, "valid": 1, "total": 1, "rate": 1.0})
            self.assertEqual(trial["product_recall"]["missing"], ["help"])
            self.assertEqual(trial["architecture_recall"]["rate"], 1.0)
            self.assertTrue(trial["parity"]["errors"])
            (stamp / "upper/trial-2/project/implementation/src/main.rs").write_text("fn main() {}\n")
            report = agent_eval.grade(stamp)
            self.assertIn("changed after the freeze", report["trials"][1]["error"])
            self.assertEqual(report["summary"]["upper"], {**report["summary"]["upper"], "pass_at_k": True, "pass_hat_k": False})


if __name__ == "__main__":
    unittest.main()
