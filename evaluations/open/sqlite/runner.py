"""Run multi-step sqlite3 scenarios in one fixed sandbox and compare two executables."""

import base64
import os
from pathlib import Path
import shutil
import signal
import subprocess

EVALUATIONS = next(path for path in Path(__file__).resolve().parents if (path / "harness.py").is_file())
SANDBOX = EVALUATIONS.parent / "work/sandbox/sqlite"  # A fixed path keeps paths in the output stable.
MAGIC = b"SQLite format 3\0"


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
    process = subprocess.Popen(["sqlite3", *args], executable=str(binary), cwd=SANDBOX, env=environment(), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT if merge else subprocess.PIPE, start_new_session=True)
    error = None
    try:
        stdout, stderr = process.communicate(stdin, timeout=timeout)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)
        stdout, stderr = process.communicate()
        error = "timeout"
    return {"returncode": process.returncode, "stdout": stdout, "stderr": stderr or b"", "error": error}


def snapshot():
    return {path.relative_to(SANDBOX).as_posix(): path.read_bytes() for path in sorted(SANDBOX.rglob("*")) if path.is_file()}


def database(name, data):
    return data.startswith(MAGIC) or name.endswith(("-journal", "-wal", "-shm"))


def text(data):
    return data.decode("utf-8", "replace")


def play(binary, scenario):
    """Run each step of a scenario. A step is an argument list and its standard input."""
    reset({name: base64.b64decode(value) for name, value in scenario.get("files", {}).items()})
    steps = [invoke(binary, step["args"], step.get("stdin", "").encode()) for step in scenario["steps"]]
    return steps, snapshot()


def outcome(steps, files):
    """Keep the exact observable result. Database files keep only their names."""
    return {"steps": [{key: text(value) if isinstance(value, bytes) else value for key, value in step.items()} for step in steps], "files": {name: None if database(name, data) else text(data) for name, data in files.items()}}


def sessions(reference, candidate, scenarios):
    """Compare the steps and the files. Byte-identical database files are a separate metric."""
    report = {"status": "passed", "passed": 0, "failed": 0, "identical_databases": 0, "databases": 0, "cases": []}
    for scenario in scenarios:
        expected, actual = (play(binary, scenario) for binary in (reference, candidate))
        passed = outcome(*expected) == outcome(*actual) and not any(step["error"] for step in expected[0] + actual[0])
        names = [name for name, data in expected[1].items() if data.startswith(MAGIC)]
        identical = sum(expected[1][name] == actual[1].get(name) for name in names)
        report["databases"] += len(names)
        report["identical_databases"] += identical
        report["passed" if passed else "failed"] += 1
        report["cases"].append({"id": scenario["id"], "passed": passed, "identical_databases": identical, **({} if passed else {"input": scenario, "reference": outcome(*expected), "candidate": outcome(*actual)})})
    report["status"] = "failed" if report["failed"] else "passed"
    return report


def crossread(reference, candidate, scenarios):
    """Each executable reads the database file that the other writes."""
    report = {"status": "passed", "passed": 0, "failed": 0, "identical_databases": 0, "databases": 0, "cases": []}

    def read(binary, data, script):
        reset({"x.db": data})
        return outcome([invoke(binary, ["x.db"], script.encode())], {})["steps"][0]

    for scenario in scenarios:
        written = {}
        for label, binary in (("reference", reference), ("candidate", candidate)):
            reset()
            step = invoke(binary, ["x.db"], scenario["write"].encode())
            written[label] = (snapshot().get("x.db", b""), text(step["stdout"]), text(step["stderr"]))
        check = "PRAGMA integrity_check;\n" + scenario["read"]
        dump = check + ".dump\n"
        records = {
            "candidate-written": (read(reference, written["candidate"][0], dump), read(reference, written["reference"][0], dump)),
            "reference-written": (read(candidate, written["reference"][0], check), read(reference, written["reference"][0], check)),
            "writer-output": (written["candidate"][1:], written["reference"][1:]),
        }
        failures = [name for name, (actual, expected) in records.items() if actual != expected]
        if not records["candidate-written"][0]["stdout"].startswith("ok\n"):
            failures.append("integrity_check")
        identical = written["candidate"][0] == written["reference"][0]
        report["databases"] += 1
        report["identical_databases"] += identical
        report["passed" if not failures else "failed"] += 1
        report["cases"].append({"id": scenario["id"], "passed": not failures, "identical_database": identical, **({"failures": failures, "input": scenario, "records": records} if failures else {})})
    report["status"] = "failed" if report["failed"] else "passed"
    return report
