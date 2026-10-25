import base64
import hashlib
import importlib.util
from pathlib import Path
import re
import sys
import tempfile
import unittest
from unittest import mock

import yaml


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("zenity_run", ROOT / "evaluations/open/zenity/run.py")
zenity = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(zenity)
HASHES = {"reference": "a" * 64, "candidate": "b" * 64}


class CaptureTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        cases = yaml.safe_load((ROOT / "evaluations/open/zenity/cases.yaml").read_text())
        review = {"capture_method": "host-native CUA", "cases": {}}
        for case in cases:
            args = case["args"]
            ax = "".join(f"  {args[args.index(flag) + 1]}\n" for flag in ("--title", "--text") if flag in args)
            ax += "  text field\n" * case["id"].startswith("entry") + "".join(f"  {index} button {name}\n" for index, name in enumerate(case["expect"]["buttons"]))
            for role, value in HASHES.items():
                files = {"ax": (f"{case['id']}-{role}-ax.txt", ax.encode()), "screenshot": (f"{case['id']}-{role}.png", b"\x89PNG\r\n\x1a\nimage")}
                result = {"case": {"id": case["id"], "args": args}, "executable_sha256": value, "capture_method": "host-native CUA", **{key: case["expect"][key] for key in ("returncode", "stdout_b64", "stderr_b64")}}
                for field, (name, data) in files.items():
                    (self.directory / name).write_bytes(data)
                    result.update({field + "_file": name, field + "_sha256": hashlib.sha256(data).hexdigest()})
                self.write(f"{case['id']}-{role}.yaml", result)
            review["cases"][case["id"]] = dict.fromkeys(("status", "focus", "title", "icon", "family", "controls"), "passed")
        self.write("visual-review.yaml", review)

    def write(self, name, value):
        (self.directory / name).write_text(yaml.safe_dump(value))

    def change(self, name, update):
        value = yaml.safe_load((self.directory / name).read_text())
        update(value)
        self.write(name, value)

    def test_matching_captures_pass(self):
        self.assertEqual(zenity.verify(self.directory, HASHES)["passed"], 5)

    def test_other_candidate_fails(self):
        with self.assertRaisesRegex(ValueError, "different executable"):
            zenity.verify(self.directory, {**HASHES, "candidate": "c" * 64})

    def test_changed_process_result_fails(self):
        self.change("entry-accept-candidate.yaml", lambda item: item.update(stdout_b64=base64.b64encode(b"other\n").decode()))
        with self.assertRaisesRegex(ValueError, "process result"):
            zenity.verify(self.directory, HASHES)

    def test_changed_raw_capture_fails(self):
        with (self.directory / "info-accept-candidate-ax.txt").open("a") as stream:
            stream.write("changed")
        with self.assertRaisesRegex(ValueError, "missing or changed"):
            zenity.verify(self.directory, HASHES)

    def test_failed_visual_review_fails(self):
        self.change("visual-review.yaml", lambda item: item["cases"]["info-accept"].update(focus="failed"))
        with self.assertRaisesRegex(ValueError, "visual parity"):
            zenity.verify(self.directory, HASHES)

    def test_unexplained_screenshot_difference_fails(self):
        (self.directory / "question-accept-candidate.png").write_bytes(b"\x89PNG\r\n\x1a\nother")
        self.change("question-accept-candidate.yaml", lambda item: item.update(screenshot_sha256=hashlib.sha256(b"\x89PNG\r\n\x1a\nother").hexdigest()))
        with self.assertRaisesRegex(ValueError, "no reviewed explanation"):
            zenity.verify(self.directory, HASHES)


class HarnessTests(unittest.TestCase):
    def test_system_reference_rejects_a_different_os_build(self):
        harness = zenity.harness
        with tempfile.TemporaryDirectory() as directory, mock.patch.object(harness.subprocess, "check_output", return_value="new\n"):
            binary = Path(directory) / "reference"
            binary.write_bytes(b"unchanged")
            with self.assertRaisesRegex(ValueError, "operating system build"):
                harness.reference("system", {"path": str(binary), "sha256": harness.digest(binary.read_bytes()), "os_build": "old"})

    def test_quality_controls_and_witness_reports(self):
        harness = zenity.harness
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "implementation").mkdir()
            binary = root / "implementation/Cargo.toml"
            binary.write_bytes(b"binary")
            for quality, controls in (({}, ["The negative control passes."]), ({"commands": [{"command": ["cargo", "fmt"], "returncode": 1, "log": "fmt.log"}]}, []), ({}, [])):
                reports = {"replay": {"status": "passed" if quality or controls else "failed", "passed": int(bool(quality or controls)), "failed": 0 if quality or controls else 2, "cases": [] if quality or controls else [{"input": {"id": "shared/case"}, "passed": False}, {"id": "custom/case", "passed": False}]}}
                with mock.patch.multiple(harness, reference=lambda *args: binary, rust=lambda *args: (binary, quality)), mock.patch.object(harness.project_helper, "status", return_value={}), mock.patch.object(harness.subprocess, "run", return_value=mock.Mock(stdout="")), mock.patch.object(sys, "argv", ["score", "--project", directory, "--output", str(root / "score")]), mock.patch("builtins.print"):
                    self.assertEqual(harness.run("control", {"sha256": "pin"}, lambda *args: (reports, controls)), 1)
                result = yaml.safe_load((root / "score/report.yaml").read_text())
                self.assertEqual((result["status"], result["reports"]["replay"]["passed"]), ("failed", int(bool(quality or controls))))
                self.assertEqual([(item["id"], Path(item["report"]).name, Path(item["report"]).is_file()) for item in result["witnesses"]["replay"]], [] if quality or controls else [("shared/case", "replay.yaml", True), ("custom/case", "replay.yaml", True)])

    def test_quality_failure_does_not_block_release_build(self):
        harness = zenity.harness
        messages = b'{"executable": "candidate", "target": {"kind": ["bin"]}}\n'
        runs = [mock.Mock(returncode=code, stdout=output, stderr=b"") for code, output in ((1, b""), (0, b""), (0, b"test result: ok. 2 passed"), (0, messages))]
        with tempfile.TemporaryDirectory() as directory, mock.patch.object(harness.subprocess, "run", side_effect=runs):
            binary, checks = harness.rust(Path(directory), Path(directory) / "logs")
        self.assertEqual((binary, checks["rust_tests"], [item["returncode"] for item in checks["commands"]]), (Path("candidate"), 2, [1, 0, 0, 0]))

    def test_doom_rejects_a_changed_resource(self):
        scorer = zenity.harness.load("doom_score", ROOT / "evaluations/open/doom/run.py")
        with tempfile.TemporaryDirectory() as directory, self.assertRaisesRegex(ValueError, "resource hash"):
            reference = Path(directory) / "doomgeneric"
            (reference.parent / "freedoom1.wad").write_bytes(b"changed")
            scorer.score(reference, reference, Path(directory))

    def test_doom_manual_gaps_block_full_score(self):
        scorer = zenity.harness.load("doom_score", ROOT / "evaluations/open/doom/run.py")
        groups = {"replay-core": [], "replay-complete": []}
        with mock.patch.object(scorer, "PIN", {}), mock.patch.multiple(scorer, milestones=lambda: groups, generate=lambda: [], upstream=lambda wad: {}), mock.patch.multiple(scorer.runner, Wad=lambda path: None, compare=lambda *args: {"status": "failed" if args[1].name.startswith("wrong-") else "passed", "passed": 1, "failed": 0}):
            reports, failures = scorer.score(Path("reference"), Path("candidate"), Path("project"))
        self.assertTrue(all(report["status"] == "passed" for report in reports.values()))
        self.assertEqual(sum("no verified manual evidence" in failure for failure in failures), len(scorer.MANUAL))

    def test_sqlite_rejects_different_database_bytes(self):
        runner = zenity.harness.load("sqlite_runner", ROOT / "evaluations/open/sqlite/runner.py")
        step = {"returncode": 0, "stdout": b"ok\n", "stderr": b"", "error": None}
        files = [{"x.db": b"SQLite format 3\0" + suffix} for suffix in (b"one", b"two")]
        with mock.patch.object(runner, "play", side_effect=[([step], data) for data in files]):
            self.assertEqual(runner.sessions(None, None, [{"id": "bytes"}])["failed"], 1)
        with mock.patch.multiple(runner, reset=lambda *args: None, invoke=lambda *args: step), mock.patch.object(runner, "snapshot", side_effect=files):
            self.assertEqual(runner.crossread(None, None, [{"id": "bytes", "write": "", "read": ""}])["failed"], 1)

    def test_grading_patterns_compile(self):
        for path in (ROOT / "evaluations").rglob("grading.yaml"):
            for rows in yaml.safe_load(path.read_text()).values():
                for row in rows:
                    with self.subTest(path=path, identifier=row["id"]):
                        re.compile(row["pattern"])

    def test_iconutil_normalization_keeps_file_metadata(self):
        with mock.patch.dict(sys.modules, cases=zenity.harness.load("iconutil_cases", ROOT / "evaluations/closed/iconutil/cases.py")):
            scorer = zenity.harness.load("iconutil_score", ROOT / "evaluations/closed/iconutil/run.py")
        with tempfile.TemporaryDirectory() as directory:
            binaries = [Path(directory) / name for name in ("reference", "candidate")]
            for binary, mode in zip(binaries, ("644", "600")):
                binary.write_text(f"#!/bin/sh\nprintf x > out\nchmod {mode} out\n")
                binary.chmod(0o755)
            report = scorer.harness.compare.compare(*binaries, [{"id": "usage/mode", "args": []}], name="iconutil")
            self.assertEqual(scorer.settle(report)["failed"], 1)


if __name__ == "__main__":
    unittest.main()
