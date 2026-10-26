"""Test comparisons with real child processes."""

import base64
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("compare", ROOT / "skills/rustify-probe/scripts/compare.py")
compare = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(compare)
sys.modules["compare"] = compare
FUZZ = importlib.util.spec_from_file_location("fuzz", ROOT / "skills/rustify-probe/scripts/fuzz.py")
fuzz = importlib.util.module_from_spec(FUZZ)
FUZZ.loader.exec_module(fuzz)


def encoded(value):
    return base64.b64encode(value).decode("ascii")


class CompareTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        self.reference = self.program("reference", "import os,stat,sys\nassert all(stat.S_ISFIFO(os.fstat(fd).st_mode) for fd in (0,1,2))\nsys.stdout.buffer.write(sys.stdin.buffer.read())\n")
        self.case = {"id": "binary", "args": [], "stdin_b64": encoded(b"\x00\xff\r\n")}

    def tearDown(self):
        self.directory.cleanup()

    def test_file_ownership_mode_and_kept_time_are_part_of_the_view(self):
        keep = self.program("keep", "import shutil\nshutil.copy2('in', 'out')\n")
        case = {"id": "copy", "args": [], "files": {"in": encoded(b"data")}}
        for field, call, before, after in [("mtime", "utime('out', None)", "fixture", "new"),
                *[("gid", f"chown('out', -1, {gid})", os.getgid(), gid) for gid in os.getgroups() if gid != os.getgid()][:1]]:
            touch = self.program("touch", f"import os,shutil\nshutil.copy2('in', 'out')\nos.{call}\n")
            report = compare.compare(keep, touch, [case], name="copy", timeout=30)
            files = {label: report["cases"][0][label]["files"]["out"] for label in ("reference", "candidate")}
            self.assertEqual((files["reference"][field], files["candidate"][field], files["reference"]["mode"], files["reference"]["uid"], files["candidate"]["uid"]), (before, after, "644", os.getuid(), os.getuid()))
            self.assertIn("files", report["cases"][0]["differences"])

    def program(self, name, body):
        path = self.root / name
        path.write_text("#!" + sys.executable + "\n" + body)
        path.chmod(0o755)
        return path

    def test_supervisor_limits_memory_children_and_streams(self):
        programs = [
            ("allocate", "import time\nx=[]\nwhile True:\n x.append(bytearray(1024*1024))\n time.sleep(.005)\n", {"memory_mib": 48}, "memory"),
            ("children", "import subprocess,time\np=subprocess.Popen(['/bin/sleep','10'],start_new_session=True)\ntime.sleep(10)\n", {"process_limit": 1}, "process"),
            ("output", "import os\nwhile True: os.write(1,b'x'*65536)\n", {"output_mib": 1}, "output"),
        ]
        for name, body, limits, message in programs:
            with self.subTest(name=name):
                result, error, metrics = compare.execute([str(self.program(name, body))], timeout=3, **limits)
                self.assertIn(message + " limit", error)
                self.assertNotEqual(result.returncode, 0)
                self.assertLessEqual(len(result.stdout), limits.get("output_mib", 16) * 1024 * 1024)
                self.assertGreaterEqual(metrics["peak_processes"], 1)
                self.assertTrue(any(row["pid"] == metrics["pid"] and row["command"] and row["started"] for row in metrics["peak_memory_processes"]))

    def test_oversized_files_do_not_enter_memory(self):
        program = self.program("large-file", "with open('out', 'wb') as stream: stream.truncate(1024**3)\n")
        result = compare.run(program, "large-file", {"id": "large-file", "args": []}, 30)
        self.assertEqual(result["error"], "The files exceeded the capture limit.")
        self.assertEqual(result["files"], {})

    def test_stdin_can_stay_open_after_delivery(self):
        program = self.program("stdin-policy", "import os,select,sys\nif len(sys.argv)>1: os.read(0,1)\nprint(bool(select.select([0],[],[],.1)[0]))\n")
        for data in (b"", b"x"):
            for keep in (False, True):
                result, error, _ = compare.execute([str(program), *(["read"] if data else [])], stdin=data, keep_stdin_open=keep, timeout=3)
                self.assertEqual((result.returncode, error, result.stdout), (0, None, b"False\n" if keep else b"True\n"))

    def test_failed_spawn_hook_cleans_up_the_process(self):
        started = []
        def reject(process):
            started.append(process.pid)
            raise RuntimeError("The watcher did not start.")
        with self.assertRaisesRegex(RuntimeError, "watcher"):
            compare.execute([str(self.program("hook", "import time\ntime.sleep(10)\n"))], on_spawn=reject, timeout=3)
        with self.assertRaises(ProcessLookupError):
            os.kill(started[0], 0)

    def test_binary_data_and_fixture_files_match(self):
        self.case["env"] = {"LC_ALL": "C", "LANG": "C", "TZ": "UTC0"}
        self.case["files"] = {"nested/data": encoded(b"\x00\xff")}
        report = compare.compare(self.reference, self.reference, [self.case], timeout=30)
        self.assertEqual(report["status"], "passed", report)
        self.assertEqual(report["cases"][0]["reference"]["stdout_b64"], self.case["stdin_b64"])
        self.assertEqual(report["cases"][0]["reference"]["files"]["nested/data"]["data_b64"], encoded(b"\x00\xff"))

    def test_differences_are_separate(self):
        candidates = {
            "stdout_b64": "print('different')\n",
            "stderr_b64": "import sys\nsys.stdout.buffer.write(sys.stdin.buffer.read())\nsys.stderr.write('different')\n",
            "returncode": "import sys\nsys.stdout.buffer.write(sys.stdin.buffer.read())\nsys.exit(3)\n",
            "files": "import sys\nsys.stdout.buffer.write(sys.stdin.buffer.read())\nopen('out', 'wb').write(b'different')\n",
        }
        for field, body in candidates.items():
            with self.subTest(field=field):
                candidate = self.program(field, body)
                report = compare.compare(self.reference, candidate, [self.case], timeout=30)
                self.assertEqual(report["status"], "failed")
                self.assertEqual(report["cases"][0]["differences"], [field], report)

    def test_execution_errors_are_not_fuzz_divergences(self):
        bad = self.program("bad", "")
        bad.write_text("#!/this-interpreter-does-not-exist\n")
        for program, timeout in [
            (self.program("slow", "import time\ntime.sleep(10)\n"), 0.05),
            (bad, 30),
            (self.program("link", "import os\nos.symlink('/tmp', 'link')\n"), 30),
        ]:
            with self.subTest(program=program.name):
                report = compare.compare(program, program, [self.case], timeout=timeout)
                self.assertEqual((report["status"], report["failed"]), ("failed", 1))
                self.assertIn("execution_error", report["cases"][0]["differences"])
                report = fuzz.fuzz(program, program, [self.case], iterations=1, timeout=timeout)
                self.assertEqual((report["status"], report["divergences"], len(report["errors"])), ("invalid", [], 1))
                self.assertEqual(report["errors"][0]["input"]["id"], "fuzz-0-0")
                self.assertIn("execution_error", report["errors"][0]["differences"])
                self.assertTrue(all(report["errors"][0][label]["error"] for label in ("reference", "candidate")))

    def test_timeout_kills_descendants(self):
        marker = self.root / "escaped"
        body = "import subprocess, sys, time\nsubprocess.Popen([sys.executable, '-c', \"import time; time.sleep(0.8); open(\" + repr(str(marker)) + \", 'w').write('leak')\"], start_new_session=True)\ntime.sleep(10)\n"
        slow = self.program("descendants", body)
        report = compare.compare(slow, self.reference, [self.case], timeout=0.5)
        self.assertEqual(report["status"], "failed")
        time.sleep(1)
        self.assertFalse(marker.exists())

    def test_invalid_cases_fail(self):
        invalid = [[], {}, [self.case, self.case], [{"id": "x", "args": [], "stdin_b64": "!"}], [{"id": "x", "args": "bad"}]]
        for name in ("../escape", "/absolute", "a/../escape", "./file", "a//b", "a\\b"):
            invalid.append([{"id": "x", "args": [], "files": {name: ""}}])
        invalid.append([{"id": "x", "args": [], "files": {"a": "", "a/b": ""}}])
        invalid.append([{"id": "x", "args": [], "env": {"HOME": "wrong"}}])
        for cases in invalid:
            with self.subTest(cases=cases), self.assertRaises(ValueError):
                compare.compare(self.reference, self.reference, cases)

    def test_invalid_timeout_fails(self):
        for timeout in (0, -1, float("inf"), float("nan")):
            with self.subTest(timeout=timeout), self.assertRaises(ValueError):
                compare.compare(self.reference, self.reference, [self.case], timeout=timeout)
        self.assertTrue(all(fuzz.fuzz(self.reference, self.reference, [self.case], iterations=count)["status"] == "invalid" for count in (0, -1)))

    def test_cli_writes_report_and_returns_failure(self):
        cases = self.root / "cases.yaml"
        report = self.root / "report.yaml"
        cases.write_text("[]")
        result = subprocess.run([sys.executable, str(ROOT / "skills/rustify-probe/scripts/compare.py"), "--reference", str(self.reference), "--candidate", str(self.reference), "--cases", str(cases), "--report", str(report)], capture_output=True)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(yaml.safe_load(report.read_text())["status"], "error")

    def test_fuzz_finds_divergence_and_keeps_reproducer(self):
        candidate = self.program("candidate", "import sys\ndata = sys.stdin.buffer.read()\nsys.stdout.buffer.write(data + (b'!' if len(data) > 4 else b''))\n")
        seeds = [{"id": "seed", "args": [], "stdin_b64": encoded(b"ab")}]
        report = fuzz.fuzz(self.reference, candidate, seeds, iterations=40, seed=1, timeout=30)
        self.assertEqual(report["status"], "failed")
        self.assertIn("stdout_b64", report["divergences"][0]["differences"])
        self.assertEqual(compare.compare(self.reference, candidate, [report["divergences"][0]["input"]], timeout=30)["failed"], 1)
        self.assertEqual(fuzz.fuzz(self.reference, self.reference, seeds, iterations=10, timeout=30)["status"], "passed")


if __name__ == "__main__":
    unittest.main()
