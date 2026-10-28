"""Run multi-step sqlite3 scenarios in one fixed sandbox and compare two executables."""

import base64
import os
from pathlib import Path
import shutil

import harness

EVALUATIONS = next(path for path in Path(__file__).resolve().parents if (path / "harness.py").is_file())
SANDBOX = EVALUATIONS.parent / "work/sandbox/sqlite"  # A fixed path keeps paths in the output stable.


def environment():
    return {"LC_ALL": "C", "LANG": "C", "TZ": "UTC", "HOME": str(SANDBOX), "PATH": "/usr/bin:/bin"}


def reset(files=None):
    """Create an empty sandbox and write the fixture files."""
    shutil.rmtree(SANDBOX, ignore_errors=True)
    SANDBOX.mkdir(parents=True)
    for name, data in (files or {}).items():
        (SANDBOX / name).parent.mkdir(parents=True, exist_ok=True)
        (SANDBOX / name).write_bytes(data)


def invoke(binary, args, stdin=b"", merge=False, timeout=30):
    """Run the binary in the sandbox. A merged run sends stderr into the stdout stream."""
    result, error, _ = harness.compare.execute(["sqlite3", *args], executable=str(binary), cwd=SANDBOX, env=environment(), stdin=stdin, preexec_fn=(lambda: os.dup2(1, 2)) if merge else None, timeout=timeout)
    return {"returncode": result.returncode, "stdout": result.stdout, "stderr": result.stderr, "error": error, "file_modes": {path.relative_to(SANDBOX).as_posix(): path.stat().st_mode & 0o7777 for path in SANDBOX.rglob("*") if path.is_file()}}


def snapshot():
    return {path.relative_to(SANDBOX).as_posix(): path.read_bytes() for path in sorted(SANDBOX.rglob("*")) if path.is_file()}


def play(binary, scenario):
    """Run each step of a scenario. A step is an argument list and its standard input."""
    reset({name: base64.b64decode(value) for name, value in scenario.get("files", {}).items()})
    steps = [invoke(binary, step["args"], step.get("stdin", "").encode()) for step in scenario["steps"]]
    return steps, snapshot()


def sessions(reference, candidate, scenarios):
    """The comparison checks the steps and all file bytes."""
    report = {"status": "passed", "passed": 0, "failed": 0, "cases": []}
    for scenario in scenarios:
        expected, actual = (play(binary, scenario) for binary in (reference, candidate))
        passed = expected == actual and not any(step["error"] for step in expected[0] + actual[0])
        report["passed" if passed else "failed"] += 1
        report["cases"].append({"id": scenario["id"], "passed": passed, **({} if passed else {"input": scenario, "reference": {"steps": expected[0], "files": expected[1]}, "candidate": {"steps": actual[0], "files": actual[1]}})})
    report["status"] = "failed" if report["failed"] else "passed"
    return report


def crossread(reference, candidate, scenarios):
    """Each executable reads the database file that the other writes."""
    report = {"status": "passed", "passed": 0, "failed": 0, "cases": []}

    def read(binary, data, script):
        reset({"x.db": data})
        return invoke(binary, ["x.db"], script.encode())

    for scenario in scenarios:
        written = {}
        for label, binary in (("reference", reference), ("candidate", candidate)):
            reset()
            step = invoke(binary, ["x.db"], scenario["write"].encode())
            written[label] = (snapshot().get("x.db", b""), step["stdout"], step["stderr"], step.get("file_modes", {}))
        check = "PRAGMA integrity_check;\n" + scenario["read"]
        dump = check + ".dump\n"
        records = {
            "database-bytes": (written["candidate"][0], written["reference"][0]),
            "candidate-written": (read(reference, written["candidate"][0], dump), read(reference, written["reference"][0], dump)),
            "reference-written": (read(candidate, written["reference"][0], check), read(reference, written["reference"][0], check)),
            "writer-output": (written["candidate"][1:], written["reference"][1:]),
        }
        failures = [name for name, (actual, expected) in records.items() if actual != expected]
        if not records["candidate-written"][0]["stdout"].startswith(b"ok\n"):
            failures.append("integrity_check")
        report["passed" if not failures else "failed"] += 1
        report["cases"].append({"id": scenario["id"], "passed": not failures, **({"failures": failures, "input": scenario, "records": records} if failures else {})})
    report["status"] = "failed" if report["failed"] else "passed"
    return report
