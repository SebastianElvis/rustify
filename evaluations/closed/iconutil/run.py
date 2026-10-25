#!/usr/bin/env python3
"""Score an iconutil reconstruction against the pinned macOS system binary."""

import base64
import io
from pathlib import Path
import plistlib
import re
import struct
import sys
import tempfile

import yaml

ROOT = Path(__file__).resolve().parent
sys.path[:0] = [str(ROOT), str(next(path for path in ROOT.parents if (path / "harness.py").is_file()))]
import harness
import cases

PIN = yaml.safe_load((ROOT / "reference.yaml").read_text())
TIMEOUT = 30
PNG = b"\x89PNG\r\n\x1a\n"
# The README records the evidence for each variable-output rule.
NSLOG = re.compile(rb"^\d{4}-\d\d-\d\d \d\d:\d\d:\d\d\.\d{3} iconutil\[\d+:[0-9a-f]+\] ", re.M)
UNDEFINED = {"icns-to-iconset/png-ic05": "a.iconset/icon_32x32.png", "icns-to-iconset/png-icp6": "a.iconset/icon_48x48.png", "image-validation/png-icp6-wrong-size": "a.iconset/icon_48x48.png"}
KNOWN = {"info", "TOC ", "icnV", "name"} | set(cases.PNG_TYPES) | {"is32", "s8mk", "il32", "l8mk", "ih32", "h8mk", "it32", "t8mk", "ICN#", "ics#", "icl8", "icl4", "ics8", "ics4"}


def unpack(data):
    out, i = bytearray(), 0
    while i < len(data):
        count, i = data[i], i + 1
        out += data[i:i + count + 1] if count < 128 else data[i:i + 1] * (count - 125)
        i += count + 1 if count < 128 else 1
    return bytes(out)


def check_png(data, size=None):
    """Decode one PNG with Pillow and return the problems."""
    from PIL import Image
    try:
        image = Image.open(io.BytesIO(data))
        image.load()
    except Exception as error:  # Pillow raises many exception types for bad data.
        return [f"Pillow rejects the PNG: {error}"]
    return [] if size is None or image.size == (size, size) else [f"The PNG is {image.size}, not {size}x{size}."]


def check_icns(data):
    """Check the container with a parser from the public ICNS description and with Pillow."""
    from PIL.IcnsImagePlugin import IcnsFile
    if data[:4] != b"icns" or len(data) < 8 or struct.unpack(">I", data[4:8])[0] != len(data):
        return ["The icns header is wrong."]
    problems, offset = [], 8
    while offset < len(data):
        kind, size = data[offset:offset + 4].decode("latin-1"), struct.unpack(">I", data[offset + 4:offset + 8].rjust(4, b"\0"))[0]
        body, offset = data[offset + 8:offset + size], offset + max(size, 8)
        side = cases.PNG_TYPES.get(kind, (0, 1))
        if size < 8 or offset > len(data):
            return problems + [f"The {kind} entry length is wrong."]
        if body.startswith(PNG):
            problems += [f"{kind}: {item}" for item in check_png(body, side[0] * side[1] or None)]
        elif body.startswith(b"ARGB") and 4 * (side[0] * side[1]) ** 2 not in (len(body) - 4, len(unpack(body[4:]))):
            problems.append(f"The {kind} ARGB data has the wrong length.")
        elif kind == "info":
            try:
                plistlib.loads(body)
            except Exception as error:  # plistlib raises several exception types.
                problems.append(f"The info entry is not a property list: {error}")
        elif kind not in KNOWN:
            problems.append(f"The {kind} entry type is unknown.")
    try:
        container = IcnsFile(io.BytesIO(data))
        for size in container.itersizes():
            if container.getimage(size).size != (size[0] * size[2], size[1] * size[2]):
                problems.append(f"Pillow reads a wrong size for {size}.")
    except Exception as error:  # Pillow raises many exception types for bad data.
        problems.append(f"Pillow rejects the icns file: {error}")
    return problems


def check_outputs(report):
    """The check compares output formats with the reference parser results."""
    rows = []
    for row in report["cases"]:
        inputs = row["input"].get("files", {})
        for path, item in row["candidate"]["files"].items():
            if inputs.get(path) == item["data_b64"] or not (path.endswith((".icns", ".licns")) or (path.endswith(".png") and ".iconset/" in path)):
                continue
            check = check_png if path.endswith(".png") else check_icns
            problems = check(base64.b64decode(item["data_b64"]))
            original = row["reference"]["files"].get(path)
            expected = check(base64.b64decode(original["data_b64"])) if original else []
            rows.append({"id": f"{row['input']['id']}/{path}", "problems": problems, "reference_problems": expected, "passed": not problems or (original is not None and set(problems) <= set(expected))})
    return rows


def chain(executable, scenario):
    """Run each step in one directory so that later steps read the outputs of earlier steps."""
    files, steps = {name: cases.encode(data) for name, data in scenario["files"].items()}, []
    for args in scenario["steps"]:
        result = harness.compare.run(executable, "iconutil", {"args": args, "files": files, "env": scenario.get("env", {})}, TIMEOUT)
        files = {name: item["data_b64"] for name, item in result["files"].items()}
        steps.append(result)
    return steps


def entries(data):
    found, offset = [], 8
    while offset + 8 <= len(data):
        size = struct.unpack(">I", data[offset + 4:offset + 8])[0]
        found.append((data[offset:offset + 4].decode("latin-1"), data[offset + 8:offset + size]))
        offset += max(size, 8)
    return found


def properties(steps):
    """Check the round-trip promises: PNG entries survive icns to iconset to icns without change."""
    files = {name: base64.b64decode(item["data_b64"]) for name, item in steps[-1]["files"].items()}
    first, second = entries(files.get("x1.icns", b"")), entries(files.get("x2.icns", b""))
    problems = [] if first else ["The first round trip writes no icns file."]
    if [kind for kind, _ in first] != [kind for kind, _ in second]:
        problems.append("The second icns file has other entries or another order.")
    for kind, body in first:
        if body.startswith(PNG) or kind == "info":
            if dict(second).get(kind) != body:
                problems.append(f"The {kind} entry changes in the second round trip.")
            size, scale = cases.PNG_TYPES.get(kind, (0, 1))
            if kind != "info" and files.get(f"s1.iconset/{cases.name(size, scale)}") != body:
                problems.append(f"The iconset file for {kind} differs from the entry.")
    return problems


def metamorphic(reference, candidate):
    rows = []
    for scenario in cases.chains():
        pair = {label: chain(binary, scenario) for label, binary in (("reference", reference), ("candidate", candidate))}
        differences = [f"step {index + 1}: {field}" for index, (left, right) in enumerate(zip(pair["reference"], pair["candidate"])) for field in ("returncode", "stdout_b64", "stderr_b64", "files", "error") if left[field] != right[field] or (field == "error" and left[field])]
        problems = {label: properties(steps) for label, steps in pair.items()}
        rows.append({"id": scenario["id"], "steps": scenario["steps"], "env": scenario.get("env", {}), "differences": differences, "properties": problems, "passed": not differences and not problems["candidate"] and not problems["reference"]})
    return rows


def settle(report):
    """Apply the declared variable-output rules to the failed cases and count the cases again."""
    for row in report["cases"]:
        if row["passed"] or any(row[side]["error"] for side in ("reference", "candidate")):
            continue
        views, path = [], UNDEFINED.get(row["input"]["id"])
        for side in ("reference", "candidate"):
            files = {name: {key: value for key, value in item.items() if key != "data_b64"} for name, item in row[side]["files"].items()}
            if path in files:
                data = base64.b64decode(row[side]["files"][path]["data_b64"])
                files[path]["sha256"] = data[8:33] if data.startswith(PNG) else data
            views.append((row[side]["returncode"], row[side]["stdout_b64"], NSLOG.sub(b"", base64.b64decode(row[side]["stderr_b64"])), files))
        if views[0] == views[1]:
            rules = ["undefined-pixels"] if "files" in row["differences"] else []
            row.update(passed=True, variable=rules + (["nslog-prefix"] if "stderr_b64" in row["differences"] else []), differences=[])
    report["passed"] = sum(row["passed"] for row in report["cases"])
    report["failed"] = len(report["cases"]) - report["passed"]
    report["status"] = "passed" if not report["failed"] else "failed"
    return report


def summary(rows):
    passed = sum(row["passed"] for row in rows)
    return {"status": "passed" if rows and passed == len(rows) else "failed", "passed": passed, "failed": len(rows) - passed, "cases": rows}


def score(reference, candidate, project):
    groups = {
        "replay-core": cases.core(), "replay-sizes": cases.sizes(), "replay-images": cases.images(), "replay-legacy": cases.legacy(),
        "replay-environment": cases.environment(), "replay-catalog": cases.catalogs(), "surface-manual": cases.manual(), "generate-random": cases.generate(),
    }
    reports = {name: settle(harness.compare.compare(reference, candidate, items, timeout=TIMEOUT, name="iconutil")) for name, items in groups.items()}
    reports["parsers-format"] = summary([row for name in groups for row in check_outputs(reports[name])])
    reports["metamorphic-roundtrip"] = summary(metamorphic(reference, candidate))
    reports["repeatability"] = settle(harness.compare.compare(reference, reference, [item for items in groups.values() for item in items], timeout=TIMEOUT, name="iconutil"))
    failures = []
    with tempfile.TemporaryDirectory() as directory:
        wrong = Path(directory) / "iconutil"
        wrong.write_text('#!/bin/sh\nprintf "Usage: iconutil --convert ( icns | iconset) [--output file] file [icon-name]\\n"\nexit 1\n')
        wrong.chmod(0o755)
        if harness.compare.compare(reference, wrong, groups["replay-core"], timeout=TIMEOUT, name="iconutil")["status"] != "failed":
            failures.append("The wrong-output control passes.")
    return reports, failures


if __name__ == "__main__":
    raise SystemExit(harness.run("iconutil", PIN, score))
