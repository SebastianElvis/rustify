#!/usr/bin/env python3
"""The gate derives parity results from the ledger, the evidence, and recorded comparisons."""

import argparse
import hashlib
import os
from pathlib import Path
import re

import yaml


DIMENSIONS = {"product", "ux", "data", "behavior"}
SURFACE = {"option", "name", "environment", "diagnostic", "input", "condition", "state", "interface"}
PATTERNS = {
    "ubiquitous": r"The .+ shall .+\.",
    "event": r"When .+, the .+ shall .+\.",
    "state": r"While .+, the .+ shall .+\.",
    "unwanted": r"If .+, then the .+ shall .+\.",
    "optional": r"Where .+, the .+ shall .+\.",
    "complex": r"(While|When|If|Where) .+, (then )?the .+ shall .+\.",
}
METHODS = {"test", "inspection", "analysis", "demonstration"}
CLASSES = {"observed", "inferred", "unknown"}
DOCUMENTS = (
    ("requirements", ("recovered/product.md", "recovered/ux.md")),
    ("components", ("recovered/architecture.md",)),
    ("components", ("implementation/docs/design.md",)),
)


def file(root, name):
    path = Path(name)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError("An input must stay inside the project.")
    if path.as_posix() in {"recovered/state.yaml", "verification/parity.yaml"}:
        raise ValueError("Operational state and gate output cannot be parity inputs.")
    path = root / path
    for parent in (path, *path.parents):
        if parent == root:
            break
        if parent.is_symlink():
            raise ValueError("An input cannot use a symlink.")
    if not path.is_file():
        raise ValueError(f"The input is missing: {name}")
    return path


def read(root, name, inputs, parse=True):
    data = file(root, name).read_bytes()
    inputs[name] = hashlib.sha256(data).hexdigest()
    return yaml.safe_load(data) if parse else data.decode(errors="replace")


def records(values, key="id"):
    if not isinstance(values, list):
        raise ValueError("A record collection must be a list.")
    result = {}
    for value in values:
        identity = value[key]
        if not isinstance(identity, str) or not identity or identity in result:
            raise ValueError("Record identifiers must be nonempty and unique.")
        result[identity] = value
    return result


def module(path):
    path = Path(path)
    name = path.parent.name if path.name == "mod.rs" else path.stem
    return None if name in {"main", "lib"} else name


def reflexion(root, model, components, inputs):
    mapped = {}
    for item in model["correspondences"]:
        if item["original"] in mapped:
            raise ValueError("Each original component needs exactly one correspondence.")
        if not item["rust"].startswith("implementation/src/") or not item["rust"].endswith(".rs"):
            raise ValueError("A correspondence must name one Rust source file.")
        read(root, item["rust"], inputs, False)
        mapped[item["original"]] = item["rust"]
    owners = {}
    for identity, path in mapped.items():
        owners.setdefault(path, []).append(identity)
    expected = {}
    for edge in records(model["edges"]).values():
        if edge["source"] not in components or edge["target"] not in components or edge["kind"] not in {"control", "data", "static"}:
            raise ValueError(f"The edge has an invalid component or kind: {edge['id']}")
        pair = (mapped.get(edge["source"]), mapped.get(edge["target"]))
        if edge["kind"] != "data" and None not in pair and pair[0] != pair[1]:
            expected[pair] = edge["id"]
    uses = set()
    for path in owners:
        text = (root / path).read_text(errors="replace")
        uses.update((path, other) for other in owners if other != path and module(other) and re.search(rf"\b{re.escape(module(other))}::", text))
    sources = {path.relative_to(root).as_posix() for path in (root / "implementation/src").rglob("*.rs")}
    return {
        "convergences": sorted(identity for pair, identity in expected.items() if pair in uses),
        "absences": sorted(identity for pair, identity in expected.items() if pair not in uses),
        "divergences": sorted(f"{source} -> {target}" for source, target in uses if (source, target) not in expected),
        "merged": sorted(path for path, names in owners.items() if len(names) > 1),
        "unmapped": sorted(set(components) - set(mapped)),
        "extra_modules": sorted(path for path in sources - set(owners) if module(path)),
    }


def check(project, comparisons=("verification/comparison.yaml",), allow_partial=False):
    root = Path(project).resolve()
    result = {"status": "failed", "assessment": "incomplete", "full_parity_gate_pass": False, "semantic_truth_verified": False, "inputs": {}, "errors": [], "gaps": []}
    try:
        inputs = result["inputs"]
        model = read(root, "recovered/model.yaml", inputs)
        evidence = records(read(root, "recovered/evidence.yaml", inputs))
        tests = records(read(root, "recovered/tests.yaml", inputs))
        target = result["target_sha256"] = yaml.safe_load((root / "recovered/state.yaml").read_text())["target"]["sha256"]
        if not isinstance(target, str) or not re.fullmatch(r"[0-9a-f]{64}", target):
            raise ValueError("The original identity must be a lowercase SHA-256 value.")
        for item in evidence.values():
            if item["classification"] not in CLASSES:
                raise ValueError(f"The evidence has an invalid classification: {item['id']}")
            if item["classification"] == "observed":
                read(root, item["path"], inputs, False)
                if inputs[item["path"]] != item["sha256"]:
                    raise ValueError(f"The evidence file hash differs: {item['id']}")
        base = root / "implementation"
        for directory, folders, files in os.walk(base):
            folders[:] = [name for name in folders if name != ".git" and (Path(directory) != base or name != "target")]
            for name in files:
                read(root, (Path(directory) / name).relative_to(root).as_posix(), inputs, False)
        cases = {}
        for name in comparisons:
            report = read(root, name, inputs)
            if report["executables"]["reference"]["sha256"] != target:
                raise ValueError("The comparison uses a different original identity.")
            rows = records([{**case, "id": case.get("id", case.get("input", {}).get("id"))} for case in report["cases"]])
            if not rows or type(report["passed"]) is not int or report["passed"] + report["failed"] != len(rows) or report["passed"] != sum(case.get("passed") is True and case.get("differences") == [] for case in rows.values()):
                raise ValueError("The comparison totals are inconsistent.")
            if set(rows) & set(cases):
                raise ValueError("A scenario appears in two comparison reports.")
            cases.update(rows)
        components = records(model["components"])
        requirements = records(model["requirements"])
        open_gaps = {identity: gap for identity, gap in records(model["gaps"]).items() if gap["status"] == "open"}
        gaps = [f"{identity}: The gap remains open." for identity in open_gaps]

        def bound(reference, owner):
            if reference not in evidence:
                raise ValueError(f"{owner}: An evidence reference is unresolved.")
            return evidence[reference]["classification"] == "observed"

        for kind, item in [("component", item) for item in components.values()] + [("edge", item) for item in records(model["edges"]).values()]:
            if item["classification"] not in CLASSES or (kind == "component" and item["level"] not in {"container", "component"}):
                raise ValueError(f"The {kind} has an invalid level or classification: {item['id']}")
            observations = [bound(name, item["id"]) for name in item["evidence"]]
            if item["classification"] != "observed" or not observations or not all(observations):
                gaps.append(f"{item['id']}: The {kind} remains uncertain.")
        structure = result["reflexion"] = reflexion(root, model, components, inputs)
        gaps += [f"{item}: The reflexion check reports {kind.replace('_', ' ')}." for kind in ("absences", "divergences", "merged", "unmapped", "extra_modules") for item in structure[kind]]
        statuses = {}
        for identity, item in requirements.items():
            pattern = PATTERNS.get(item["pattern"])
            if item["dimension"] not in DIMENSIONS or item["classification"] not in CLASSES or item["verification"] not in METHODS:
                raise ValueError(f"{identity}: The requirement has an invalid dimension, classification, or method.")
            if pattern is None or not re.fullmatch(pattern, item["statement"]) or item["statement"].count(" shall ") != 1 or "{{" in item["statement"]:
                raise ValueError(f"{identity}: The statement does not follow its EARS pattern.")
            if set(item["components"]) - set(components):
                raise ValueError(f"{identity}: The requirement names an unknown component.")
            reasons = []
            mismatch = False
            if item["classification"] != "observed" or not item["evidence"] or not all(bound(name, identity) for name in item["evidence"]):
                reasons.append("The original behavior remains uncertain.")
            reasons += [f"The gap {name} remains open." for name, gap in open_gaps.items() if identity in gap["items"]]
            if item["verification"] != "test":
                if not item["records"] or not all(bound(name, identity) for name in item["records"]):
                    reasons.append(f"The {item['verification']} record is missing or uncertain.")
            elif not item["tests"]:
                reasons.append("The requirement has no test.")
            for test_id in item["tests"] if item["verification"] == "test" else ():
                test = tests[test_id]
                if test["origin"] not in {"observed", "inferred", "proposed"} or not isinstance(test["expect"], dict) or not test["expect"] or not test.get("scenarios"):
                    raise ValueError(f"{test_id}: A test needs a valid origin, scenarios, and exact expectations.")
                if not test.get("evidence") or not all(bound(name, test_id) for name in test["evidence"]):
                    reasons.append(f"{test_id}: The expected result remains uncertain.")
                for scenario in test["scenarios"]:
                    case = cases.get(scenario)
                    if case is None:
                        reasons.append(f"{scenario}: The scenario has no executed capture.")
                        continue
                    for label in ("reference", "candidate"):
                        actual = case[label]
                        if actual.get("error") is not None or any(name not in actual or yaml.safe_dump(actual[name]) != yaml.safe_dump(value) for name, value in test["expect"].items()):
                            reasons.append(f"{scenario}/{label}: An exact expected assertion fails.")
                            mismatch = mismatch or label == "candidate"
                    if case.get("passed") is not True:
                        reasons.append(f"{scenario}: The recorded comparison fails.")
                        mismatch = True
            statuses[identity] = "passed" if not reasons else "failed" if mismatch else "incomplete"
            gaps += [f"{identity}: {reason}" for reason in reasons]
        surface = records(model["surface"])
        for identity, item in surface.items():
            if item["kind"] not in SURFACE or set(item["requirements"]) - set(requirements):
                raise ValueError(f"{identity}: The surface item has an invalid kind or an unknown requirement.")
            if not item["requirements"]:
                gaps.append(f"{identity}: No requirement covers the surface item.")
        if not surface:
            gaps.append("The surface inventory is empty.")
        result["surface"] = {kind: sum(item["kind"] == kind for item in surface.values()) for kind in sorted(SURFACE)}
        for kind, names in DOCUMENTS:
            text = "".join(read(root, name, inputs, False) for name in names)
            gaps += [f"{identity}: {' or '.join(names)} does not name this item." for identity in (requirements if kind == "requirements" else components) if not re.search(rf"\b{re.escape(identity)}\b", text)]
        roadmap = read(root, "recovered/roadmap.md", inputs, False)
        gaps += [f"{name}: recovered/roadmap.md does not name this open gap." for name in open_gaps if name not in roadmap]
        if model["inventory"]["complete"] is not True:
            gaps.append("The original inventory remains incomplete.")
        result["gaps"] = sorted(set(gaps))
        result["requirements"] = statuses
        result["slices"] = {item["id"]: all(statuses.get(name) == "passed" for name in item["requirements"]) for item in model["slices"]}
        result["dimensions"] = {name: {status: sum(requirements[key]["dimension"] == name and value == status for key, value in statuses.items()) for status in ("passed", "failed", "incomplete")} for name in sorted(DIMENSIONS)}
        if not gaps:
            result.update(status="passed", assessment="full_parity_pass", full_parity_gate_pass=True)
        elif "failed" in statuses.values():
            result["assessment"] = "failed"
        if result["status"] != "passed" and allow_partial:
            result["status"] = "partial"
    except (OSError, ValueError, KeyError, TypeError, AttributeError, yaml.YAMLError) as error:
        result["errors"].append(str(error))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True)
    parser.add_argument("--comparison", action="append")
    parser.add_argument("--report", required=True)
    parser.add_argument("--allow-partial", action="store_true")
    args = parser.parse_args()
    result = check(args.project, args.comparison or ["verification/comparison.yaml"], args.allow_partial)
    path = Path(args.report)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(result))
    print(yaml.safe_dump({key: result[key] for key in ("status", "assessment", "errors")} | {"gaps": len(result["gaps"])}, sort_keys=False), end="")
    return 0 if result["status"] in {"passed", "partial"} and not result["errors"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
