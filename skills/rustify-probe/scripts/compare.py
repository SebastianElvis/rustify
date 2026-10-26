#!/usr/bin/env python3
"""Compare two CLI programs with the same cases."""

import argparse
import base64
import ctypes
from concurrent.futures import ThreadPoolExecutor
from contextlib import suppress
import hashlib
import math
import os
from pathlib import Path, PurePosixPath
import signal
import selectors
import stat
import subprocess
import struct
import sys
import tempfile
import threading
import time

import yaml


FIXTURE_TIME = 1_000_000_000


def decode(value):
    if not isinstance(value, str):
        raise ValueError("A base64 value must be a string.")
    return base64.b64decode(value, validate=True)


def validate(cases):
    if not isinstance(cases, list) or not cases:
        raise ValueError("Cases must be a nonempty list.")
    ids = set()
    for case in cases:
        if not isinstance(case, dict) or set(case) - {"id", "args", "stdin_b64", "files", "env"}:
            raise ValueError("A case contains invalid fields.")
        identity = case.get("id")
        if not isinstance(identity, str) or not identity or identity in ids:
            raise ValueError("Each case must have a unique nonempty id.")
        ids.add(identity)
        args = case.get("args")
        if not isinstance(args, list) or any(not isinstance(a, str) or "\0" in a for a in args):
            raise ValueError("Case arguments must be strings without NUL bytes.")
        decode(case.get("stdin_b64", ""))
        files = case.get("files", {})
        if not isinstance(files, dict):
            raise ValueError("Case files must be an object.")
        for name, data in files.items():
            if not isinstance(name, str):
                raise ValueError("A fixture path must be a string.")
            path = PurePosixPath(name)
            if not name or "\0" in name or "\\" in name or path.is_absolute() or any(p in {"", ".", ".."} for p in name.split("/")):
                raise ValueError("A fixture path must be a safe relative file path.")
            if any(str(parent) in files for parent in path.parents if str(parent) != "."):
                raise ValueError("Fixture files cannot contain other fixture files.")
            decode(data)
        env = case.get("env", {})
        if not isinstance(env, dict):
            raise ValueError("Case environment values must be an object.")
        for key, value in env.items():
            if not isinstance(key, str) or not key or "=" in key or "\0" in key or not isinstance(value, str) or "\0" in value:
                raise ValueError("Case environment values must be valid strings.")
            if key in {"HOME", "PATH"}:
                raise ValueError("A case cannot replace the controlled environment.")
    return cases


def capture_files(root, metadata=None):
    files, size = {}, 0
    for path in sorted(root.rglob("*")):
        status = path.lstat()
        if stat.S_ISDIR(status.st_mode):
            continue
        if not stat.S_ISREG(status.st_mode):
            raise ValueError("A process produced a symlink or a special file.")
        size += status.st_size
        if size > 64 * 1024 * 1024:
            raise ValueError("The files exceeded the capture limit.")
        if metadata is not None:
            metadata[path.relative_to(root).as_posix()] = {"mtime_ns": status.st_mtime_ns, "ctime_ns": status.st_ctime_ns, "atime_ns": status.st_atime_ns, "device": status.st_dev, "inode": status.st_ino, "links": status.st_nlink}
        files[path.relative_to(root).as_posix()] = {
            "sha256": hashlib.sha256(data := path.read_bytes()).hexdigest(), "data_b64": base64.b64encode(data).decode("ascii"),
            "mode": format(stat.S_IMODE(status.st_mode), "o"), "mtime": "fixture" if status.st_mtime_ns == FIXTURE_TIME * 10**9 else "new", "uid": status.st_uid, "gid": status.st_gid,
        }
    return files


def execute(command, *, timeout, stdin=b"", keep_stdin_open=False, on_spawn=None, memory_mib=512, output_mib=16, process_limit=64, **options):
    """Run observed descendants with sampled limits and bounded pipe captures."""
    if not math.isfinite(timeout) or timeout <= 0 or any(type(value) is not int or value <= 0 for value in (memory_mib, output_mib, process_limit)):
        raise ValueError("Resource limits must be positive and finite.")
    usage = ctypes.CDLL("/usr/lib/libproc.dylib").proc_pid_rusage if sys.platform == "darwin" else None
    if usage:
        usage.argtypes, usage.restype = [ctypes.c_int, ctypes.c_int, ctypes.c_void_p], ctypes.c_int
    peak, footprint, count, error = 0, 0, 0, None
    output = {"stdout": bytearray(), "stderr": bytearray()}
    remaining, size = memoryview(stdin), 0
    start, owned, peak_details = time.monotonic(), {}, []
    process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True, **options)
    def members():
        rows = subprocess.check_output(["/bin/ps", "-axo", "pid=,ppid=,pgid=,rss=,lstart=,comm="], text=True)
        parts = [row.split(maxsplit=9) for row in rows.splitlines()]
        tasks = {int(p[0]): (int(p[1]), int(p[2]), int(p[3]), " ".join(p[4:9]), p[9] if len(p) > 9 else "") for p in parts}
        active = {pid for pid, (_, group, _, born, _) in tasks.items() if group == process.pid or owned.get(pid) == born}
        while active != (expanded := active | {pid for pid, (parent, _, _, _, _) in tasks.items() if parent in active}):
            active = expanded
        owned.update({pid: tasks[pid][3] for pid in active})
        return {pid: {"pid": pid, "parent_pid": tasks[pid][0], "started": tasks[pid][3], "command": tasks[pid][4], "rss_kib": tasks[pid][2]} for pid in active}
    with process, selectors.DefaultSelector() as selector, ThreadPoolExecutor(max_workers=1) as workers:
        for stream, mode, name in ((process.stdin, selectors.EVENT_WRITE, "stdin"), (process.stdout, selectors.EVENT_READ, "stdout"), (process.stderr, selectors.EVENT_READ, "stderr")):
            os.set_blocking(stream.fileno(), False)
            if name != "stdin" or remaining:
                selector.register(stream, mode, name)
            elif not keep_stdin_open:
                stream.close()
        stop = threading.Event()
        def supervise():
            nonlocal peak, footprint, count, peak_details, error
            try:
                while not stop.is_set():
                    current = members()
                    for pid, row in current.items():
                        info = ctypes.create_string_buffer(160)
                        physical = struct.unpack_from("=Q", info, 72)[0] // 1024 if usage and usage(pid, 2, info) == 0 else 0
                        row["memory_kib"] = max(row["rss_kib"], physical)
                    memory = sum(row["memory_kib"] for row in current.values())
                    if memory > footprint:
                        peak_details = list(current.values())
                    peak, footprint, count = max(peak, sum(row["rss_kib"] for row in current.values())), max(footprint, memory), max(count, len(current))
                    for value, limit, label in ((memory, memory_mib * 1024, "memory"), (len(current), process_limit, "process"), (time.monotonic() - start, timeout, "time")):
                        if value > limit:
                            error = error or f"The process exceeded the {label} limit."
                    if error or stop.wait(0.05):
                        break
            finally:
                process.kill()
                for pid in members():
                    with suppress(ProcessLookupError):
                        os.kill(pid, signal.SIGKILL)
        monitor = workers.submit(supervise)
        try:
            if on_spawn is not None:
                on_spawn(process)
            while not (error or monitor.done()) and (selector.get_map() or process.poll() is None):
                for key, _ in selector.select(0.05):
                    try:
                        if key.data == "stdin":
                            remaining = remaining[os.write(key.fd, remaining[:65536]):]
                            if remaining:
                                continue
                        elif chunk := os.read(key.fd, 65536):
                            output[key.data].extend(chunk[:max(0, output_mib * 1024 * 1024 - size)])
                            size += len(chunk)
                            if size > output_mib * 1024 * 1024:
                                error = "The process group exceeded the output limit."
                            continue
                    except BrokenPipeError:
                        pass
                    selector.unregister(key.fileobj)
                    if key.data != "stdin" or not keep_stdin_open:
                        key.fileobj.close()
        finally:
            stop.set()
        monitor.result()
    result = subprocess.CompletedProcess(command, process.returncode, bytes(output["stdout"]), bytes(output["stderr"]))
    return result, error, {"pid": process.pid, "peak_rss_kib": peak, "peak_memory_kib": footprint, "peak_memory_processes": peak_details, "memory_method": "RSS and physical footprint" if usage else "RSS", "peak_processes": count, "memory_mib": memory_mib, "output_mib": output_mib, "process_limit": process_limit}


def run(executable, name, case, timeout):
    result = {"returncode": None, "stdout_b64": "", "stderr_b64": "", "files": {}, "file_metadata": {}, "error": None}
    with tempfile.TemporaryDirectory(prefix="rustify-") as directory:
        root = Path(directory)
        for filename, data in case.get("files", {}).items():
            path = root / filename
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(decode(data))
            path.chmod(0o644)
            os.utime(path, (FIXTURE_TIME, FIXTURE_TIME))
        env = {"LC_ALL": "C", "LANG": "C", "TZ": "UTC", "HOME": directory, "PATH": "/usr/bin:/bin"}
        env.update(case.get("env", {}))
        try:
            completed, error, metrics = execute(
                [name, *case["args"]], executable=str(executable), cwd=root, env=env,
                stdin=decode(case.get("stdin_b64", "")), timeout=timeout,
            )
            result.update(returncode=completed.returncode, stdout_b64=base64.b64encode(completed.stdout).decode("ascii"), stderr_b64=base64.b64encode(completed.stderr).decode("ascii"), error=error, resources=metrics)
        except OSError as error:
            result["error"] = str(error)
        try:
            result["files"] = capture_files(root, result["file_metadata"])
        except (OSError, ValueError) as error:
            result["error"] = str(error)
    return result


def differ(results):
    differences = [field for field in ("returncode", "stdout_b64", "stderr_b64", "files") if results["reference"][field] != results["candidate"][field]]
    if any(result["error"] is not None for result in results.values()):
        differences.append("execution_error")
    return differences


def compare(reference, candidate, cases, timeout=5, name=None):
    validate(cases)
    if not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("The time limit must be positive and finite.")
    name = Path(reference).name if name is None else name
    if not isinstance(name, str) or not name or "\0" in name:
        raise ValueError("The program name must be nonempty and contain no NUL bytes.")
    report, paths = {"status": "passed", "passed": 0, "failed": 0, "program_name": name, "executables": {}, "cases": []}, {}
    for label, value in (("reference", reference), ("candidate", candidate)):
        path = Path(value).resolve(strict=True)
        if not path.is_file() or not os.access(path, os.X_OK):
            raise ValueError("Each executable must be a runnable regular file.")
        paths[label] = path
        report["executables"][label] = {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
    for case in cases:
        results = {label: run(path, name, case, timeout) for label, path in paths.items()}
        differences = differ(results)
        passed = not differences
        report["passed" if passed else "failed"] += 1
        report["cases"].append({"input": case, **results, "differences": differences, "passed": passed})
    if report["failed"]:
        report["status"] = "failed"
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference", required=True)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--cases", required=True)
    parser.add_argument("--report", required=True)
    parser.add_argument("--timeout", type=float, default=5)
    parser.add_argument("--name", help="The default is the original filename.")
    args = parser.parse_args()
    try:
        cases = yaml.safe_load(Path(args.cases).read_text())
        report = compare(args.reference, args.candidate, cases, args.timeout, args.name)
    except (OSError, ValueError, yaml.YAMLError) as error:
        report = {"status": "error", "passed": 0, "failed": 0, "error": str(error), "cases": []}
    destination = Path(args.report)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(yaml.safe_dump(report, sort_keys=False))
    print(yaml.safe_dump({key: report[key] for key in ("status", "passed", "failed")}, sort_keys=False), end="")
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
