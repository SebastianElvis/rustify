"""Run multi-step Ninja scenarios and compare the steps of two executables."""

import os
from pathlib import Path
import signal
import struct
import subprocess
import tempfile
import time

BASE = 946684800  # The runner gives every fixture file the mtime 2000-01-01T00:00:00Z.


def encode(text):
    return text.encode("utf-8", "surrogateescape")


def decode(data):
    return data.decode("utf-8", "surrogateescape")


def build_log(data):
    """Mask the start time, the end time, and the nonzero mtime of each build log entry."""
    lines = []
    for line in decode(data).split("\n"):
        fields = line.split("\t")
        if len(fields) == 5 and not line.startswith("#"):
            fields[:3] = ["*", "*", "0" if fields[2] == "0" else "*"]
        lines.append("\t".join(fields))
    return "\n".join(lines)


def deps_log(data):
    """Mask the nonzero output mtime of each deps log record."""
    data, offset = bytearray(data), 16
    while offset + 4 <= len(data):
        size = struct.unpack_from("<I", data, offset)[0]
        if size >> 31 and offset + 16 <= len(data) and struct.unpack_from("<Q", data, offset + 8)[0]:
            struct.pack_into("<Q", data, offset + 8, 1)
        offset += 4 + (size & 0x7FFFFFFF)
    return decode(bytes(data))


def snapshot(root):
    files = {}
    for path in sorted(root.rglob("*")):
        name = path.relative_to(root).as_posix()
        if path.is_symlink() or not (path.is_file() or path.is_dir()):
            raise ValueError(f"The build produced a special file: {name}")
        if path.is_dir():
            files[name + "/"] = None
            continue
        data = path.read_bytes()
        files[name] = build_log(data) if path.name == ".ninja_log" else deps_log(data) if path.name == ".ninja_deps" else decode(data)
    return files


def prepare(root, step, now):
    for name, text in step.get("write", {}).items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(encode(text))
        os.utime(path, (BASE, BASE))
    for name in step.get("remove", []):
        (root / name).unlink()
    for name, seconds in step.get("mtime", {}).items():
        os.utime(root / name, (seconds, seconds))
    for name in step.get("touch", []):
        os.utime(root / name, ns=(now, now))


def execute(executable, root, step, timeout):
    """Run one Ninja step and return its normalized result."""
    env = {"LC_ALL": "C", "LANG": "C", "TZ": "UTC", "HOME": str(root), "PATH": "/usr/bin:/bin", "TERM": "dumb", **step.get("env", {})}
    result = {"returncode": None, "stdout": "", "stderr": "", "error": None}
    process = subprocess.Popen(["ninja", *step["args"]], executable=str(executable), cwd=root, env=env, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT if step.get("merge") else subprocess.PIPE, start_new_session=True)
    try:
        if "signal" in step:
            deadline = time.monotonic() + timeout
            while not (root / step["wait"]).exists() and time.monotonic() < deadline and process.poll() is None:
                time.sleep(0.01)
            time.sleep(0.1)
            process.send_signal(step["signal"])
        stdout, stderr = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)
        stdout, stderr = process.communicate()
        result["error"] = "The step exceeded the time limit."
    finally:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    places = sorted({str(root), os.path.realpath(root)}, key=len, reverse=True)
    for label, data in (("stdout", stdout), ("stderr", stderr or b"")):
        text = decode(data)
        for place in places:
            text = text.replace(place, "$ROOT")
        result[label] = text
    result["returncode"] = process.returncode
    return result


def play(executables, scenario, timeout=10):
    """Run each step with the executable at the same position and record the results."""
    steps = []
    with tempfile.TemporaryDirectory(prefix="rustify-ninja-") as directory:
        root = Path(directory)
        prepare(root, {"write": scenario.get("files", {})}, 0)
        for index, step in enumerate(scenario["steps"]):
            prepare(root, step, time.time_ns())
            record = {"executable": executables[index % len(executables)][0], **execute(executables[index % len(executables)][1], root, step, timeout)}
            try:
                record["files"] = snapshot(root)
            except (OSError, ValueError) as error:
                record["error"] = record["error"] or str(error)
            steps.append(record)
    return steps


def compare(expected, actual, scenarios, timeout=10):
    """Compare two executable schedules on each scenario and report the differing steps."""
    report = {"status": "passed", "passed": 0, "failed": 0, "cases": []}
    for scenario in scenarios:
        results = {"expected": play(expected, scenario, timeout), "actual": play(actual, scenario, timeout)}
        differences = [f"step {index}: {field}" for index, (left, right) in enumerate(zip(results["expected"], results["actual"])) for field in ("returncode", "stdout", "stderr", "files") if left.get(field) != right.get(field)]
        differences += [f"step {index}: {step['error']}" for side in results.values() for index, step in enumerate(side) if step["error"]]
        passed = not differences
        report["passed" if passed else "failed"] += 1
        report["cases"].append({"input": scenario, **results, "differences": differences, "passed": passed})
    report["status"] = "failed" if report["failed"] else "passed"
    return report
