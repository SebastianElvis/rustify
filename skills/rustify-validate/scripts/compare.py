#!/usr/bin/env python3
"""Compare two CLI programs with the same cases."""

import argparse
import base64
import hashlib
import math
import os
from pathlib import Path, PurePosixPath
import signal
import stat
import subprocess
import tempfile

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
            if key in {"HOME", "LANG", "LC_ALL", "TZ", "PATH"}:
                raise ValueError("A case cannot replace the controlled environment.")
    return cases


def capture_files(root):
    files = {}
    for path in sorted(root.rglob("*")):
        mode = path.lstat().st_mode
        if stat.S_ISDIR(mode):
            continue
        if not stat.S_ISREG(mode):
            raise ValueError("A process produced a symlink or a special file.")
        data, status = path.read_bytes(), path.lstat()
        files[path.relative_to(root).as_posix()] = {
            "sha256": hashlib.sha256(data).hexdigest(),
            "data_b64": base64.b64encode(data).decode("ascii"),
            "mode": format(stat.S_IMODE(status.st_mode), "o"),
            "mtime": "fixture" if int(status.st_mtime) == FIXTURE_TIME else "new",
        }
    return files


def run(executable, name, case, timeout):
    result = {"returncode": None, "stdout_b64": "", "stderr_b64": "", "files": {}, "error": None}
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
        process = None
        try:
            process = subprocess.Popen(
                [name, *case["args"]], executable=str(executable), cwd=root, env=env,
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                start_new_session=True,
            )
            try:
                stdout, stderr = process.communicate(decode(case.get("stdin_b64", "")), timeout=timeout)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                stdout, stderr = process.communicate()
                result["error"] = "The process exceeded the time limit."
            result.update(returncode=process.returncode, stdout_b64=base64.b64encode(stdout).decode("ascii"), stderr_b64=base64.b64encode(stderr).decode("ascii"))
        except OSError as error:
            result["error"] = str(error)
        finally:
            if process is not None:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except (ProcessLookupError, PermissionError):
                    pass
        try:
            result["files"] = capture_files(root)
        except (OSError, ValueError) as error:
            result["error"] = str(error)
    return result


def differ(results):
    differences = [field for field in ("returncode", "stdout_b64", "stderr_b64", "files") if results["reference"][field] != results["candidate"][field]]
    if any(result["error"] is not None for result in results.values()):
        differences.append("execution_error")
    return differences


def compare(reference, candidate, cases, timeout=5, name="base64"):
    validate(cases)
    if not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("The time limit must be positive and finite.")
    if not isinstance(name, str) or not name or "\0" in name:
        raise ValueError("The program name must be nonempty and contain no NUL bytes.")
    report = {"status": "passed", "passed": 0, "failed": 0, "executables": {}, "cases": []}
    paths = {}
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
    parser.add_argument("--name", default="base64")
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
