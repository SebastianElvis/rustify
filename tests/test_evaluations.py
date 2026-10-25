import base64
import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest

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


if __name__ == "__main__":
    unittest.main()
