"""Run multi-step Doom scenarios and compare normalized results of two executables."""

import hashlib
import os
from pathlib import Path
import re
import struct
import tempfile

import harness

PLAYER = 280
PLAYER_POINTERS = (0, 216, 228)
MOBJ = 154
MOBJ_POINTERS = (0, 4, 8, 24, 28, 44, 48, 52, 92, 120, 150)
SPECIALS = {0: 48, 1: 40, 2: 42, 3: 56, 4: 36, 5: 36, 6: 28}


class Wad:
    """The IWAD gives demo lumps and the map sizes that the savegame layout needs."""

    def __init__(self, path):
        self.path = Path(path)
        self.data = self.path.read_bytes()
        count, offset = struct.unpack_from("<ii", self.data, 4)
        self.lumps = [struct.unpack_from("<ii8s", self.data, offset + 16 * i) for i in range(count)]
        self.names = [name.rstrip(b"\0").decode("ascii", "replace") for _, _, name in self.lumps]

    def lump(self, name, after=0):
        index = self.names.index(name, after)
        position, size, _ = self.lumps[index]
        return self.data[position:position + size], index

    def map_sizes(self, episode, level):
        _, marker = self.lump(f"E{episode}M{level}")
        lines, _ = self.lump("LINEDEFS", marker)
        sectors, _ = self.lump("SECTORS", marker)
        sides = sum((value != -1) for i in range(0, len(lines), 14) for value in struct.unpack_from("<hh", lines, i + 10))
        return len(sectors) // 26, len(lines) // 14, sides


def savegame(data, wad):
    """Replace each saved pointer with a null flag and clear the unread count of a moving platform."""
    data = bytearray(data)

    def mask(base, offsets):
        for offset in offsets:
            struct.pack_into("<I", data, base + offset, int(struct.unpack_from("<I", data, base + offset)[0] != 0))

    sectors, lines, sides = wad.map_sizes(data[41], data[42])
    position = 50
    for present in data[43:47]:
        if present:
            position += -position & 3
            mask(position, PLAYER_POINTERS)
            position += PLAYER
    position += sectors * 14 + lines * 6 + sides * 10
    while data[position] == 1:
        position += 1 + (-(position + 1) & 3)
        mask(position, MOBJ_POINTERS)
        position += MOBJ
    if data[position]:
        raise ValueError("The thinker list has an unknown class.")
    position += 1
    while data[position] in SPECIALS:
        size = SPECIALS[data[position]]
        position += 1 + (-(position + 1) & 3)
        mask(position, (0, 4, 8))
        status, old = struct.unpack_from("<ii", data, position + 36)
        if size == SPECIALS[3] and 2 not in (status, old if status == 3 else status):
            struct.pack_into("<i", data, position + 32, 0)  # EV_DoPlat leaves count uninitialized. T_PlatRaise reads it only while waiting.
        position += size
    if data[position:] != b"\x07\x1d":
        raise ValueError("The savegame has no valid end.")
    return bytes(data)


def snapshot(root, wad):
    files = {}
    for path in sorted(root.rglob("*")):
        name = path.relative_to(root).as_posix()
        if path.is_symlink() or not (path.is_file() or path.is_dir()):
            raise ValueError(f"The run produced a special file: {name}")
        if path.is_dir():
            files[name + "/"] = (path.stat().st_mode & 0o7777, None)
            continue
        data = path.read_bytes()
        if path.suffix == ".dsg":
            try:
                data = savegame(data, wad)
            except (ValueError, IndexError, struct.error) as error:
                files[name] = (path.stat().st_mode & 0o7777, f"invalid savegame: {error}")
                continue
        if path.suffix in (".cfg", ".txt"):
            files[name] = (path.stat().st_mode & 0o7777, data.decode("utf-8", "surrogateescape"))
        else:
            files[name] = (path.stat().st_mode & 0o7777, f"sha256:{hashlib.sha256(data).hexdigest()} size:{len(data)}")
    return files


def normalize(stdout, stderr):
    """Apply the variable-field rules that the README declares."""
    stdout = re.sub(rb"zone memory: 0x[0-9a-f]+,", b"zone memory: 0x*,", stdout)
    stderr = re.sub(rb"in \d+ realtics \([-0-9.a-z]+ fps\)", b"in * realtics (* fps)", stderr)
    stderr = re.sub(rb"(W_GetNumForName: .* not found!\n\nWarning: recursive call to I_Error detected.\n)(?:\1)+.*", rb"\1[repeated until the stack overflows]\n", stderr, flags=re.S)
    return stdout.decode("utf-8", "surrogateescape"), stderr.decode("utf-8", "surrogateescape")


def execute(executable, wad, case):
    with tempfile.TemporaryDirectory(prefix="rustify-doom-") as directory:
        root = Path(directory)
        for name, data in case.get("files", {}).items():
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data.replace(b"{iwad}", bytes(wad.path)))
        steps = []
        for step in case["steps"]:
            env = {"LC_ALL": "C", "LANG": "C", "TZ": "UTC", "HOME": directory, "PATH": "/usr/bin:/bin", **step.get("env", {})}
            args = [arg.replace("{iwad}", str(wad.path)) for arg in step["args"]]
            result = {"returncode": None, "stdout": "", "stderr": "", "error": None}
            completed, result["error"], result["resources"] = harness.compare.execute(
                ["doomgeneric", *args], executable=str(executable), cwd=root, env=env, timeout=step.get("timeout", 30),
            )
            stdout, stderr = completed.stdout, completed.stderr
            result["returncode"] = completed.returncode
            result["stdout"], result["stderr"] = normalize(stdout, stderr)
            steps.append(result)
        try:
            files = snapshot(root, wad)
        except (OSError, ValueError) as error:
            files, steps[-1]["error"] = {}, str(error)
    return {"steps": steps, "files": files}


def compare(reference, candidate, wad, cases):
    report = {"status": "passed", "passed": 0, "failed": 0, "cases": []}
    for case in cases:
        results = {"reference": execute(reference, wad, case), "candidate": execute(candidate, wad, case)}
        views = {label: {"steps": [{key: value for key, value in step.items() if key != "resources"} for step in result["steps"]], "files": result["files"]} for label, result in results.items()}
        differences = [field for field in ("steps", "files") if views["reference"][field] != views["candidate"][field]]
        if any(step["error"] for result in results.values() for step in result["steps"]):
            differences.append("execution_error")
        passed = not differences
        report["passed" if passed else "failed"] += 1
        report["cases"].append({"id": case["id"], "steps": [step["args"] for step in case["steps"]], "files": sorted(case.get("files", {})), **results, "differences": differences, "passed": passed})
    report["status"] = "failed" if report["failed"] or not cases else "passed"
    return report
