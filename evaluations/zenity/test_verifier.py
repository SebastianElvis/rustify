"""Challenge fresh GUI proof checks without opening a dialog."""

import contextlib
import io
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

import run

from verify_fresh import verify

ROOT = Path(__file__).resolve().parent
RECOVERED = ROOT / "target/recovered"
PIN = RECOVERED / "evidence/jxa-exec-source-pin.json"
SOURCE = RECOVERED / "evidence/jxa-exec-replay"
if not SOURCE.exists():
    SOURCE = ROOT.parents[1] / "work/strict-zenity/evidence-exec"


class ProofTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.proof = self.root / "proof"
        self.recovered = self.root / "recovered"
        shutil.copytree(SOURCE, self.proof)
        self.recovered.mkdir()
        for name in ("freeze.json", "scenarios.json", "evidence.json", "tests.json"):
            shutil.copy2(RECOVERED / name, self.recovered / name)

    def change(self, name, update):
        path = self.proof / name
        value = json.loads(path.read_text())
        update(value)
        path.write_text(json.dumps(value))

    def check(self):
        return verify(self.proof, self.recovered, PIN)

    def test_real_source_bound_proof_passes(self):
        report = self.check()
        self.assertEqual((report["passed"], report["raw_identical_screenshot_pairs"]), (5, 4))

    def test_missing_case_fails(self):
        (self.proof / "info-accept-candidate.json").unlink()
        with self.assertRaises(FileNotFoundError):
            self.check()

    def test_stale_source_pin_fails(self):
        self.change("info-accept-candidate.json", lambda item: item.update(source_pin_sha256="old source"))
        with self.assertRaisesRegex(ValueError, "stale source pin"):
            self.check()

    def test_failed_focus_verdict_fails(self):
        self.change("visual-review.json", lambda item: item["cases"]["info-accept"].update(focus="failed"))
        with self.assertRaisesRegex(ValueError, "visual parity"):
            self.check()

    def test_mutated_raw_ax_fails(self):
        with (self.proof / "entry-accept-candidate-ax.txt").open("a") as stream:
            stream.write("changed")
        with self.assertRaisesRegex(ValueError, "raw capture hash"):
            self.check()

    def test_mutated_raw_screenshot_fails(self):
        with (self.proof / "info-accept-candidate.png").open("ab") as stream:
            stream.write(b"changed")
        with self.assertRaisesRegex(ValueError, "raw capture hash"):
            self.check()

    def test_declared_buttons_drive_the_check(self):
        path = self.recovered / "tests.json"
        values = json.loads(path.read_text())
        values[0]["expect"]["buttons"] = ["different control"]
        path.write_text(json.dumps(values))
        with self.assertRaisesRegex(ValueError, "buttons differ from tests.json"):
            self.check()

    def test_checkpoint_failure_cannot_report_success(self):
        destination = self.root / "verification"
        (destination / "logs").mkdir(parents=True)
        (destination / "logs/unit.log").write_text("test result: ok. 5 passed")
        pin = json.loads(PIN.read_text())
        freeze = json.loads((RECOVERED / "freeze.json").read_text())
        def progress(advance=False):
            if advance:
                raise RuntimeError("The checkpoint regression probe failed.")
            return {"completed": [], "next": "prepare", "stale": "prepare"}
        with patch.object(run, "VERIFICATION", destination), patch.object(run, "FRESH", self.root / "imported"), patch.object(run, "frozen_evidence", return_value=(freeze, {}, pin)), patch.object(run, "captured_results", return_value=5), patch.object(run, "reference"), patch.object(run, "command", return_value={"returncode": 0}), patch.object(run, "checkpoint_status", side_effect=progress), patch("sys.argv", ["run.py", "--fresh-evidence", str(self.proof)]), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(run.main(), 1)
        result = json.loads((destination / "summary.json").read_text())
        self.assertEqual(result["status"], "failed")
        self.assertIn("checkpoint regression", result["error"])


if __name__ == "__main__":
    unittest.main()
