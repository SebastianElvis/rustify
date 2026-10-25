"""Test the agent evaluation harness with a scripted agent and a private track."""

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
TRACK = "rustify-test-upper"
PROJECT = {
    "recovered/product.md": "REQ-1: The upper program shall write uppercase bytes.\n",
    "recovered/architecture.md": "C-1 is the entry component.\n",
    "implementation/Cargo.toml": '[package]\nname = "upper"\nversion = "0.1.0"\nedition = "2021"\n',
    "implementation/Cargo.lock": 'version = 3\n\n[[package]]\nname = "upper"\nversion = "0.1.0"\n',
    "implementation/src/main.rs": "use std::io::{Read, Write};\n\nfn main() {\n    let mut data = Vec::new();\n    std::io::stdin().read_to_end(&mut data).unwrap();\n    std::io::stdout()\n        .write_all(&data.to_ascii_uppercase())\n        .unwrap();\n}\n",
}
AGENT = f"""import json, re, sys
from pathlib import Path
project = Path(re.search(r"Write the target project to (.+)[.]", sys.stdin.read()).group(1))
for name, text in json.loads({json.dumps(json.dumps(PROJECT))}).items():
    (project / name).parent.mkdir(parents=True, exist_ok=True)
    (project / name).write_text(text)
"""


@unittest.skipUnless(shutil.which("cargo"), "The harness test needs cargo.")
class AgentEvaluationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.addCleanup(lambda: (ROOT / "work/downloads" / TRACK).unlink(missing_ok=True))
        self.root = Path(temporary.name)
        reference = self.root / "upper"
        reference.write_text("#!" + sys.executable + "\nimport sys\nsys.stdout.buffer.write(sys.stdin.buffer.read().upper())\n")
        reference.chmod(0o755)
        self.track = self.root / TRACK
        self.track.mkdir()
        case = {"id": "v1", "args": [], "stdin_b64": base64.b64encode(b"ab").decode()}
        (self.track / "run.py").write_text(f"""import sys
sys.path.insert(0, {str(ROOT / 'evaluations')!r})
import harness
PIN = {{"url": {reference.as_uri()!r}, "sha256": {hashlib.sha256(reference.read_bytes()).hexdigest()!r}}}

def score(reference, candidate, project):
    return {{"upstream": harness.compare.compare(reference, candidate, [{case!r}], name="upper")}}, []

if __name__ == "__main__":
    raise SystemExit(harness.run({TRACK!r}, PIN, score))
""")
        (self.track / "grading.json").write_text(json.dumps({"scope": "uppercase conversion", "features": [{"id": "uppercase", "pattern": "(?i)uppercase"}, {"id": "help", "pattern": "--help"}], "components": [{"id": "entry", "pattern": "(?i)entry"}]}))
        (self.root / "agent.py").write_text(AGENT)

    def test_scripted_agent_trials_are_frozen_and_graded(self):
        stamp = agent_eval.run([self.track], f"{sys.executable} {self.root / 'agent.py'}", 2, self.root / "out", 120)
        self.assertTrue((stamp / TRACK / "trial-1/.claude/skills/rustify/SKILL.md").is_file())
        report = agent_eval.grade(stamp)
        self.assertEqual(report["summary"][TRACK]["pass_hat_k"], True, report["trials"])
        trial = report["trials"][0]
        self.assertEqual(trial["blind_pass_rate"], 1.0)
        self.assertEqual(trial["product_recall"], {"rate": 0.5, "missing": ["help"]})
        self.assertEqual(trial["architecture_recall"]["rate"], 1.0)
        self.assertTrue(trial["parity"]["errors"])
        (stamp / TRACK / "trial-2/project/implementation/src/main.rs").write_text("fn main() {}\n")
        report = agent_eval.grade(stamp)
        self.assertIn("changed after the freeze", report["trials"][1]["error"])
        self.assertEqual((report["summary"][TRACK]["pass_at_k"], report["summary"][TRACK]["pass_hat_k"]), (True, False))


if __name__ == "__main__":
    unittest.main()
