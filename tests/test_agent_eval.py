"""Test the agent evaluation harness with a scripted agent and a private track."""

import base64
import hashlib
import importlib.util
import marshal
from pathlib import Path
import shutil
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch

import yaml

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
AGENT = f"""import re, sys
from pathlib import Path
project = Path(re.search(r"Write the target project to (.+)[.]", sys.stdin.read()).group(1))
for name, text in {PROJECT!r}.items():
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
        (self.track / "grading.yaml").write_text(yaml.safe_dump({"features": [{"id": "uppercase", "pattern": "(?i)uppercase"}, {"id": "help", "pattern": "--help"}], "components": [{"id": "entry", "pattern": "(?i)entry"}]}))
        (self.root / "agent.py").write_text(AGENT)

    def test_scripted_agent_trials_are_frozen_and_graded(self):
        stamp = agent_eval.run([self.track], f"{sys.executable} {self.root / 'agent.py'}", 2, self.root / "out", 120)
        self.assertTrue((stamp / TRACK / "trial-1/.claude/skills/rustify/SKILL.md").is_file())
        helper = stamp / TRACK / "trial-1/.agents/skills/rustify-validate/scripts/parity.py"
        cache = Path(importlib.util.cache_from_source(str(helper)))
        cache.parent.mkdir(exist_ok=True)
        payload = compile('def check(project):\n return {"assessment": "full_parity_pass", "errors": [], "gaps": []}\n', str(helper), "exec")
        cache.write_bytes(importlib.util.MAGIC_NUMBER + struct.pack("<III", 0, int(helper.stat().st_mtime), helper.stat().st_size) + marshal.dumps(payload))
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
        self.assertEqual((report["summary"][TRACK]["pass_at_k"], report["summary"][TRACK]["pass_hat_k"]), (True, False), report["trials"])
        helper.write_text('raise RuntimeError("The grader must reject this changed helper.")\n')
        report = agent_eval.grade(stamp)
        self.assertIn("installed skills changed", report["trials"][0]["error"])


class ResumeTests(unittest.TestCase):
    def test_resume_uses_only_failed_sessions(self):
        with tempfile.TemporaryDirectory() as temporary:
            stamp = Path(temporary)
            for trial, error, session in ((1, "usage_limit_reached", "saved-session"), (2, None, "done"), (3, "failed", None)):
                agent_eval.save(stamp / TRACK / f"trial-{trial}/run.yaml", {"error": error, "session": session})
            with patch.object(agent_eval, "attempt") as attempt:
                agent_eval.resume(stamp, "agent -p", 30)
            self.assertEqual(attempt.call_count, 1)
            self.assertEqual(attempt.call_args.args[2], ["agent", "-p", "--resume", "saved-session"])
            (stamp / TRACK / "trial-1/score").mkdir()
            with patch.object(agent_eval, "attempt") as attempt, self.assertRaisesRegex(ValueError, "new blind run"):
                agent_eval.resume(stamp, "agent -p", 30)
            attempt.assert_not_called()

    def test_binary_resources_reach_the_agent(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            source = ROOT / "LICENSE"
            with patch.object(agent_eval, "reference", return_value=(source, {"resources": {"README.md": "README.md"}, "forbidden_libraries": ["ClosedCodec"]})), patch.object(agent_eval, "attempt") as attempt:
                stamp = agent_eval.run([ROOT / "evaluations/open/doom"], "agent", 1, output, 1)
            self.assertEqual((stamp / "doom/trial-1/input/README.md").read_bytes(), (ROOT / "README.md").read_bytes())
            self.assertIn("ClosedCodec", attempt.call_args.args[3])

    def test_timeout_preserves_partial_output_and_session(self):
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            record = {"seconds": 1, "session": "saved-session", "cost_usd": 2}
            error = agent_eval.subprocess.TimeoutExpired(["agent"], 1)
            with patch.object(agent_eval.subprocess, "Popen") as launch, patch.object(agent_eval.os, "killpg") as kill:
                launch.return_value.communicate.side_effect = [error, ("partial output", "")]
                agent_eval.attempt(workspace, record, ["agent"], "continue", 1)
            kill.assert_called_once_with(launch.return_value.pid, agent_eval.signal.SIGKILL)
            self.assertIn("partial output", (workspace / "agent.log").read_text())
            self.assertEqual(record["session"], "saved-session")
            self.assertEqual(record["error"], "agent_failed")

    def test_success_clears_error_and_preserves_cost(self):
        with tempfile.TemporaryDirectory() as temporary:
            record = {"seconds": 1, "error": "usage_limit_reached", "session": "saved-session", "cost_usd": 2}
            with patch.object(agent_eval.subprocess, "Popen") as launch:
                launch.return_value.returncode = 0
                launch.return_value.communicate.return_value = ('{"is_error": false, "total_cost_usd": 0.5}', "")
                agent_eval.attempt(Path(temporary), record, ["agent"], "continue", 1)
            self.assertIsNone(record["error"])
            self.assertEqual(record["session"], "saved-session")
            self.assertEqual(record["cost_usd"], 2.5)


if __name__ == "__main__":
    unittest.main()
