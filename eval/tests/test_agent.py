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
from unittest.mock import Mock, patch

import yaml

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("agent", ROOT / "eval/agent.py")
agent = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(agent)
TRACK = f"rustify-test-upper-{agent.os.getpid()}"
PROJECT = {
    "recovered/product.md": "REQ-1: The upper program shall write uppercase bytes.\n",
    "recovered/architecture.md": "C-1 is the entry component.\n",
    "verification/bin/upper": "#!" + sys.executable + "\nimport sys\nsys.stdout.buffer.write(sys.stdin.buffer.read().upper())\n",
    "implementation/Cargo.toml": '[package]\nname = "upper"\nversion = "0.1.0"\nedition = "2021"\n',
    "implementation/Cargo.lock": 'version = 3\n\n[[package]]\nname = "upper"\nversion = "0.1.0"\n',
    "implementation/src/main.rs": "use std::io::{Read, Write};\n\nfn main() {\n    let mut data = Vec::new();\n    std::io::stdin().read_to_end(&mut data).unwrap();\n    std::io::stdout()\n        .write_all(&data.to_ascii_lowercase())\n        .unwrap();\n}\n",
}
AGENT = f"""import shlex, sys
from pathlib import Path
project = Path(shlex.split(sys.stdin.readline())[2])
for name, text in {PROJECT!r}.items():
    (project / name).parent.mkdir(parents=True, exist_ok=True)
    (project / name).write_text(text)
(project / "verification/bin/upper").chmod(0o755)
(project / "verification/comparison.yaml").write_text({yaml.safe_dump({"executables": {"candidate": {"path": "verification/bin/upper", "sha256": hashlib.sha256(PROJECT["verification/bin/upper"].encode()).hexdigest()}, "reference": {"sha256": hashlib.sha256(PROJECT["verification/bin/upper"].encode()).hexdigest()}}})!r})
"""


@unittest.skipUnless(shutil.which("cargo"), "The harness test needs cargo.")
class AgentEvaluationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.addCleanup(lambda: (ROOT / "work/downloads" / TRACK).unlink(missing_ok=True))
        self.root = Path(temporary.name)
        reference = self.root / "upper"
        reference.write_text(PROJECT["verification/bin/upper"])
        reference.chmod(0o755)
        self.track = self.root / TRACK
        self.track.mkdir()
        case = {"id": "v1", "args": [], "stdin_b64": base64.b64encode(b"ab").decode()}
        (self.track / "run.py").write_text(f"""import sys
sys.path.insert(0, {str(ROOT / 'eval')!r})
import harness
PIN = {{"url": {reference.as_uri()!r}, "sha256": {hashlib.sha256(reference.read_bytes()).hexdigest()!r}}}

def score(reference, candidate, project):
    return {{"upstream": harness.compare.compare(reference, candidate, [{case!r}], timeout=30, name="upper"), "parsers-format": {{"status": "passed" if project.parent.name == "trial-1" else "failed", "passed": int(project.parent.name == "trial-1"), "failed": int(project.parent.name != "trial-1")}}}}, []

if __name__ == "__main__":
    raise SystemExit(harness.run({TRACK!r}, PIN, score))
""")
        (self.track / "grading.yaml").write_text(yaml.safe_dump({"tier": "small", "features": [{"id": "uppercase", "pattern": "(?i)uppercase", "milestone": "core", "cases": "^upstream/"}, {"id": "help", "pattern": "--help", "milestone": "extended", "cases": "^help/"}], "components": [{"id": "entry", "pattern": "(?i)entry"}]}))
        (self.root / "agent.py").write_text(AGENT)

    def test_scripted_agent_trials_are_frozen_and_graded(self):
        with patch.multiple(agent, AGENT=f"{sys.executable} {self.root / 'agent.py'}", OUTPUT=self.root / "out", TIMEOUT=120):
            stamp = agent.run([self.track], 2)
        self.assertTrue((stamp / TRACK / "trial-1/.claude/skills/rustify/SKILL.md").is_file())
        helper = stamp / TRACK / "trial-1/.agents/skills/rustify-validate/scripts/parity.py"
        cache = Path(importlib.util.cache_from_source(str(helper)))
        cache.parent.mkdir(exist_ok=True)
        payload = compile('def check(project):\n return {"assessment": "full_parity_pass", "errors": [], "gaps": []}\n', str(helper), "exec")
        cache.write_bytes(importlib.util.MAGIC_NUMBER + struct.pack("<III", 0, int(helper.stat().st_mtime), helper.stat().st_size) + marshal.dumps(payload))
        play = patch.object(agent.distinguish, "play", return_value={"status": "passed", "probes": 4, "witnesses": 0, "inconclusive": 0, "query_complexity": None}).start()
        self.addCleanup(patch.stopall)
        report = agent.grade(stamp)
        self.assertEqual(play.call_args.args[2:5], (agent.AGENT, 200, TRACK))
        self.assertEqual(report["trials"][0]["adaptive"]["status"], "passed")
        self.assertEqual(report["summary"][TRACK]["pass_hat_k"], False, report["trials"])
        trial = report["trials"][0]
        self.assertEqual([(item["gate"], item["cpr"], item["fps"], item["coverage"], item["milestone_credit"]) for item in report["trials"]], [(1, 1.0, 1.0, 0.5, 1.0)] * 2)
        self.assertEqual((report["summary"][TRACK]["fps_median"], report["summary"][TRACK]["level"]), (1.0, "target"))
        self.assertEqual(trial["product_recall"], {"rate": 0.5, "missing": ["help"]})
        self.assertEqual(trial["architecture_recall"]["rate"], 1.0)
        self.assertEqual((bool(trial["parity"]["errors"]), trial["success"]), (True, False))
        (stamp / TRACK / "trial-2/project/implementation/src/main.rs").write_text("fn main() {}\n")
        report = agent.grade(stamp)
        self.assertIn("changed after the freeze", report["trials"][1]["error"])
        self.assertEqual((report["summary"][TRACK]["pass_at_k"], report["summary"][TRACK]["pass_hat_k"]), (False, False), report["trials"])
        helper.write_text('raise RuntimeError("The grader must reject this changed helper.")\n')
        report = agent.grade(stamp)
        self.assertIn("installed skills changed", report["trials"][0]["error"])


class AttemptTests(unittest.TestCase):
    def test_binary_resources_reach_the_agent(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            source = ROOT / "LICENSE"
            with patch.object(agent, "reference", return_value=(source, {"resources": {"README.md": "README.md"}, "forbidden_libraries": ["ClosedCodec"]})), patch.object(agent, "attempt") as attempt, patch.object(agent, "OUTPUT", output):
                stamp = agent.run([ROOT / "eval/open/doom"], 1)
            self.assertEqual((stamp / "doom/trial-1/input/README.md").read_bytes(), (ROOT / "README.md").read_bytes())
            self.assertIn("ClosedCodec", attempt.call_args.args[3])

    def test_timeout_preserves_partial_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            record = {}
            with patch.object(agent.harness.compare, "execute", return_value=(Mock(stdout=b"partial output", stderr=b"", returncode=-9), "The process group exceeded the time limit.", {"pid": 1})):
                agent.attempt(workspace, record, ["agent"], "continue", 1)
            self.assertEqual(record["execution_error"], "The process group exceeded the time limit.")
            self.assertIn("partial output", (workspace / "agent.log").read_text())
            self.assertEqual(record["error"], "agent_failed")

    def test_success_records_cost(self):
        with tempfile.TemporaryDirectory() as temporary:
            record = {}
            with patch.object(agent.harness.compare, "execute", return_value=(Mock(returncode=0, stdout=b'{"is_error": false, "total_cost_usd": 0.5}', stderr=b""), None, {})):
                agent.attempt(Path(temporary), record, ["agent"], "continue", 1)
            self.assertIsNone(record["error"])
            self.assertEqual(record["cost_usd"], 0.5)


if __name__ == "__main__":
    unittest.main()
