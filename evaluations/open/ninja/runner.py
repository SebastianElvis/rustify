"""Run multi-step Ninja scenarios and compare the views of two executable schedules.

The view contains stdout, stderr, the exit status, and every file after each step.
The runner applies only the equivalence rules that the README declares:
- A nanosecond timestamp inside the wall-clock window of the scenario becomes `<wall>`.
- The start and end times of each `.ninja_log` entry become `*`.
- Each `"%p"` graph node identifier becomes a number in the order of first use.
- The path of the scenario directory becomes `$ROOT`.
"""

import os
from pathlib import Path
import re
import struct
import threading
import tempfile
import time

import harness

BASE = 946684800  # The runner gives every written fixture file the mtime 2000-01-01T00:00:00Z.
SLACK = 3600 * 10**9
NUMBER = re.compile(r"\b\d{16,20}\b")
POINTER = re.compile(r'"0x[0-9a-f]+"')


def encode(text):
    return text.encode("utf-8", "surrogateescape")


def decode(data):
    return data.decode("utf-8", "surrogateescape")


def wall(text, window):
    return NUMBER.sub(lambda match: "<wall>" if window[0] - SLACK <= int(match.group()) <= time.time_ns() + SLACK else match.group(), text)


def pointers(text):
    names = {}
    return POINTER.sub(lambda match: '"node%d"' % names.setdefault(match.group(), len(names)), text)


def rooted(text, root):
    for place in sorted({str(root), os.path.realpath(root)}, key=len, reverse=True):
        text = text.replace(place, "$ROOT")
    return text


def build_log(data, window):
    lines = []
    for line in decode(data).split("\n"):
        fields = line.split("\t")
        if len(fields) == 5 and not line.startswith("#"):
            fields[:3] = ["*", "*", wall(fields[2], window)]
        lines.append("\t".join(fields))
    return "\n".join(lines)


def deps_log(data, window):
    data, offset = bytearray(data), 16
    while offset + 4 <= len(data):
        size = struct.unpack_from("<I", data, offset)[0]
        if size >> 31 and offset + 16 <= len(data) and wall(str(struct.unpack_from("<Q", data, offset + 8)[0]), window) == "<wall>":
            data[offset + 8:offset + 16] = b"<wall>\0\0"
        offset += 4 + (size & 0x7FFFFFFF)
    return decode(bytes(data))


def snapshot(root, window):
    files = {}
    for path in sorted(root.rglob("*")):
        name = path.relative_to(root).as_posix()
        if path.is_symlink() or not (path.is_file() or path.is_dir()):
            raise ValueError(f"The build produced a special file: {name}")
        if path.is_dir():
            files[name + "/"] = (path.stat().st_mode & 0o7777, None)
            continue
        data = path.read_bytes()
        files[name] = (path.stat().st_mode & 0o7777, build_log(data, window) if path.name == ".ninja_log" else deps_log(data, window) if path.name == ".ninja_deps" else rooted(decode(data), root))
    return files


def prepare(root, step):
    for name, text in step.get("write", {}).items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(encode(text))
        os.utime(path, (BASE, BASE))
    for name in step.get("remove", []):
        (root / name).unlink(missing_ok=True)
    for name, seconds in step.get("mtime", {}).items():
        os.utime(root / name, (seconds, seconds))
    now = time.time_ns()
    for name in step.get("touch", []):
        os.utime(root / name, ns=(now, now))


def execute(executable, root, step, window, timeout):
    """Run one Ninja step and return its normalized view."""
    env = {"LC_ALL": "C", "LANG": "C", "TZ": "UTC", "HOME": str(root), "PATH": "/usr/bin:/bin", "TERM": "dumb", **step.get("env", {})}
    command = ["/usr/bin/script", "-q", "/dev/null", str(executable)] if step.get("tty") else ["ninja"]
    watcher, done, marker = None, threading.Event(), [False]

    def interrupt(process):
        deadline = time.monotonic() + timeout
        while not (root / step["wait"]).exists() and time.monotonic() < deadline and process.poll() is None and not done.wait(0.01):
            pass
        marker[0] = (root / step["wait"]).exists()
        if not done.wait(0.1):
            process.send_signal(step["signal"])

    def started(process):
        nonlocal watcher
        watcher = threading.Thread(target=interrupt, args=(process,))
        watcher.start()

    try:
        completed, error, resources = harness.compare.execute(
            [*command, *step["args"]], executable=None if step.get("tty") else str(executable),
            cwd=root, env=env, timeout=timeout, keep_stdin_open=True,
            preexec_fn=(lambda: os.dup2(1, 2)) if step.get("merge") else None,
            on_spawn=started if "signal" in step else None,
        )
    finally:
        done.set()
        if watcher:
            watcher.join()
    streams = {label: pointers(wall(rooted(decode(data), root), window)) for label, data in (("stdout", completed.stdout), ("stderr", completed.stderr))}
    return {"returncode": completed.returncode, "error": error or ("The signal marker was not observed." if "signal" in step and not marker[0] else None), "resources": resources, **streams}


def play(executables, scenario, timeout=15):
    """Run step i with executable i modulo the schedule length and record each view."""
    steps = []
    window = (time.time_ns(),)
    with tempfile.TemporaryDirectory(prefix="rustify-ninja-") as directory:
        root = Path(directory)
        prepare(root, {"write": scenario.get("files", {})})
        for index, step in enumerate(scenario["steps"]):
            label, executable = executables[index % len(executables)]
            prepare(root, step)
            record = {"executable": label, **execute(executable, root, step, window, timeout)}
            try:
                record["files"] = snapshot(root, window)
            except (OSError, ValueError) as error:
                record["error"] = record["error"] or str(error)
            steps.append(record)
    return steps


def compare(expected, actual, scenarios, timeout=15):
    """Compare two executable schedules on each scenario and list the differing steps."""
    rows = []
    for scenario in scenarios:
        results = {"expected": play(expected, scenario, timeout), "actual": play(actual, scenario, timeout)}
        differences = [f"step {index}: {field}" for index, (left, right) in enumerate(zip(results["expected"], results["actual"])) for field in ("returncode", "stdout", "stderr", "files") if left.get(field) != right.get(field)]
        differences += [f"step {index}: {step['error']}" for side in results.values() for index, step in enumerate(side) if step["error"]]
        rows.append({"id": scenario["id"], "input": scenario, **results, "differences": differences, "passed": not differences})
    failed = sum(not row["passed"] for row in rows)
    return {"status": "failed" if failed else "passed", "passed": len(rows) - failed, "failed": failed, "cases": rows}
