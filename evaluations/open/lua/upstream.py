"""Run each file of the official lua-5.5.1-tests suite on both programs."""

import base64
from pathlib import Path
import tarfile

from harness import REPOSITORY, compare, load

TESTS = {"name": "lua-5.5.1-tests.tar.gz", "url": "https://www.lua.org/tests/lua-5.5.1-tests.tar.gz", "sha256": "da07b543872dc0bb2ff12aabd0c248578d78df3eb6b67efdc537a46d455c7f31"}
PORTABLE = ["-e", "_port=true _soft=true"]
# Each test file maps to one grading feature. bwcoercion.lua and tracegc.lua are helper modules that other files load.
FILES = {
    "all": "load", "api": "base-library", "attrib": "package", "big": "tables", "bitwise": "bitwise", "calls": "functions",
    "closure": "functions", "code": "binary-chunks", "constructs": "control-flow", "coroutine": "coroutines", "cstack": "error-handling",
    "db": "debug-library", "errors": "error-reporting", "events": "metatables", "files": "io-library", "gc": "garbage-collector",
    "gengc": "garbage-collector", "goto": "goto", "heavy": "numbers", "literals": "lexer", "locals": "to-be-closed", "main": "cli-options",
    "math": "math-library", "memerr": "error-handling", "nextvar": "tables", "pm": "patterns", "sort": "table-library",
    "strings": "string-library", "tpack": "string-pack", "utf8": "utf8", "vararg": "varargs", "verybig": "load",
}
MODES = {
    "all": {"user": ["-e", "_U=true", "all.lua"]},
    "big": {"portable": [*PORTABLE, "big.lua"], "full": ["-e", "local f = coroutine.wrap(assert(loadfile('big.lua'))) assert(f() == 'b') assert(f() == 'a') print('OK')"]},
    "heavy": {"full": ["heavy.lua"]},
}
TIMEOUTS = {"heavy": 900}
# The macOS reference fails these upstream checks for host reasons, so the scorer changes them.
# BLANK removes the text from a start anchor through an end anchor and keeps the line count, so line numbers stay the same.
BLANK = [
    ("files.lua", '  local f = io.output("/dev/full")', "  assert(f:close())", "macOS has no /dev/full device."),
    ("files.lua", "    {\"sh -c 'kill -s HUP $$'\", \"exit\"},", "", "The macOS /bin/sh runs the last command with exec, so the signal is visible."),
    ("files.lua", "        -- this is too much\n", "sec=60})", "The macOS mktime accepts second 60 of the maximum year."),
    ("main.lua", 'RUN("env LUA_CPATH=', 'checkout("true\\n")', "The test needs compiled C modules from libs/. Hidden visibility prevents them."),
    ("main.lua", 'local prompt = "alo"', 'XXXX\\n?$"))', "The macOS readline does not echo prompts when standard input is not a terminal."),
    ("attrib.lua", 'do  print("testing external strings")', "tt[str2] == str)\n  end\nend\n", "The test needs the compiled C module lib2-v2."),
]
REPLACE = [
    ("main.lua", 'if release >= "5.5.1" then', "if false then", "The macOS build links readline at build time and ignores LUA_READLINELIB."),
    ("attrib.lua", 'when == "absent")', 'when == "open")', 'macOS supports dlopen, so a missing library gives "open", not "absent".'),
]


def suite():
    """Read the pinned test archive and apply the host patches."""
    downloads = REPOSITORY / "work/downloads"
    downloads.mkdir(parents=True, exist_ok=True)
    archive = load("build_reference", REPOSITORY / "scripts/build_reference.py").fetch(TESTS, downloads)
    with tarfile.open(archive) as bundle:
        files = {Path(*Path(item.name).parts[1:]).as_posix(): bundle.extractfile(item).read().decode("latin-1") for item in bundle.getmembers() if item.isfile()}
    files["libs/P1/.keep"] = ""
    for name, start, end, _ in BLANK + REPLACE:
        if files[name].count(start) != 1:
            raise ValueError(f"The patch anchor is not unique in {name}: {start}")
    for name, start, end, _ in BLANK:
        text = files[name]
        first = text.index(start)
        last = text.index(end, first) + len(end) if end else first + len(start)
        files[name] = text[:first] + "\n" * text[first:last].count("\n") + text[last:]
    for name, old, new, _ in REPLACE:
        files[name] = files[name].replace(old, new)
    return {name: base64.b64encode(text.encode("latin-1")).decode("ascii") for name, text in files.items()}


def last_line(result):
    lines = [line for line in base64.b64decode(result["stdout_b64"]).decode("latin-1").splitlines() if line.strip()]
    return lines[-1] if lines else ""


def trim(result):
    """Keep the process view small: drop the copied suite and keep the output tails."""
    keep = {key: result[key] for key in ("returncode", "error")}
    for key in ("stdout_b64", "stderr_b64"):
        keep[key] = base64.b64encode(base64.b64decode(result[key])[-4000:]).decode("ascii")
    return keep


def evaluate(reference, candidate, stems=FILES):
    files = suite()
    reports = {}
    for stem in stems:
        feature = FILES[stem]
        rows = []
        for mode, args in MODES.get(stem, {"portable": [*PORTABLE, f"{stem}.lua"], "full": [f"{stem}.lua"]}).items():
            case = {"id": f"{feature}/{stem}-{mode}", "args": args, "files": files}
            row = {"id": case["id"], "args": args}
            for label, binary in (("reference", reference), ("candidate", candidate)):
                result = compare.run(binary, str(binary), case, TIMEOUTS.get(stem, 300))
                row[label] = {**trim(result), "last_line": last_line(result)}
            row["passed"] = all(row[label]["returncode"] == 0 and row[label]["error"] is None for label in ("reference", "candidate")) and row["reference"]["last_line"] == row["candidate"]["last_line"]
            rows.append(row)
        failed = sum(not row["passed"] for row in rows)
        reports[f"upstream-{stem}"] = {"status": "failed" if failed else "passed", "passed": len(rows) - failed, "failed": failed, "cases": rows}
    return reports
