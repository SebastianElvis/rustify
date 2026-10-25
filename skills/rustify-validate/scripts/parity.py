#!/usr/bin/env python3
"""The checker validates declared coverage and recorded exact assertions."""

import argparse
import hashlib
import json
import os
from pathlib import Path


DIMENSIONS = {"product", "ux", "components", "data", "behavior"}


def file(root, name):
    path = Path(name)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError("An input must stay inside the project.")
    if path.as_posix() in {"recovered/state.json", "verification/parity.json"}:
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


def read(root, name, inputs):
    data = file(root, name).read_bytes()
    inputs[name] = hashlib.sha256(data).hexdigest()
    return json.loads(data)


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


def check(project, matrix_name="verification/parity-matrix.json", allow_partial=False):
    root = Path(project).resolve()
    result = {"status": "failed", "assessment": "incomplete", "full_parity_gate_pass": False, "semantic_truth_verified": False, "inputs": {}, "errors": [], "gaps": []}
    try:
        inputs = result["inputs"]
        matrix = read(root, matrix_name, inputs)
        result["target_sha256"] = matrix["target_sha256"]
        if not isinstance(matrix["target_sha256"], str) or len(matrix["target_sha256"]) != 64 or any(char not in "0123456789abcdef" for char in matrix["target_sha256"]):
            raise ValueError("The original identity must be a lowercase SHA-256 value.")
        original = records(matrix["original_features"])
        mappings = records(matrix["mappings"], "feature")
        evidence = records(read(root, "recovered/evidence.json", inputs))
        tests = records(read(root, "recovered/tests.json", inputs))
        if any(item.get("classification") not in {"observed", "inferred", "unknown"} for item in (*original.values(), *evidence.values())):
            raise ValueError("An original claim has an invalid classification.")
        bound = records(matrix["evidence_files"])
        tree = root / "implementation"
        for directory, folders, files in os.walk(tree):
            folders[:] = [name for name in folders if name != ".git" and (Path(directory) != tree or name != "target")]
            if any((Path(directory) / name).is_symlink() for name in folders):
                raise ValueError("An implementation input cannot use a symlink.")
            for name in files:
                relative = (Path(directory) / name).relative_to(root).as_posix()
                inputs[relative] = hashlib.sha256(file(root, relative).read_bytes()).hexdigest()
        if not original:
            raise ValueError("The original feature inventory cannot be empty.")
        if set(mappings) - set(original):
            raise ValueError("A mapping names an undeclared original feature.")
        for item in bound.values():
            inputs[item["path"]] = hashlib.sha256(file(root, item["path"]).read_bytes()).hexdigest()
            if item["id"] not in evidence or inputs[item["path"]] != item["sha256"]:
                raise ValueError("An evidence identifier or file hash differs.")
        capture = matrix["comparison"]
        path = file(root, capture["path"])
        inputs[capture["path"]] = hashlib.sha256(path.read_bytes()).hexdigest()
        if inputs[capture["path"]] != capture["sha256"]:
            raise ValueError("The comparison report hash differs.")
        comparison = json.loads(path.read_text())
        cases = records([{**case, "id": case.get("id", case.get("input", {}).get("id"))} for case in comparison["cases"]])
        if comparison["executables"]["reference"]["sha256"] != matrix["target_sha256"]:
            raise ValueError("The comparison uses a different original identity.")
        if not cases or type(comparison["passed"]) is not int or type(comparison["failed"]) is not int or comparison["passed"] + comparison["failed"] != len(cases):
            raise ValueError("The comparison totals are inconsistent.")
        passed = sum(case.get("passed") is True and case.get("differences") == [] for case in cases.values())
        if comparison["passed"] != passed or comparison["status"] != ("passed" if passed == len(cases) else "failed"):
            raise ValueError("The comparison case results are inconsistent.")
        if matrix["scope"] not in {"full_product", "subset"}:
            raise ValueError("The scope must identify the full product or a subset.")
        selected = matrix["selected_features"]
        if not isinstance(selected, list) or len(selected) != len(set(selected)) or set(selected) - set(original):
            raise ValueError("Selected features must be unique original identifiers.")
        gaps = result["gaps"]
        if comparison["failed"]:
            gaps.append("The comparison contains a recorded failure.")
        if matrix["surface_complete"] is not True:
            gaps.append("The full original surface remains incomplete.")
        if matrix["scope"] != "full_product" or set(selected) != set(original):
            gaps.append("The selected subset does not cover the full original surface.")
        if matrix["scope"] == "subset" and not matrix.get("user_scope_evidence"):
            gaps.append("The subset has no recorded user authorization.")
        for identity, feature in original.items():
            if feature["classification"] != "observed":
                gaps.append(f"{identity}: The original feature remains uncertain.")
            mapping = mappings.get(identity)
            if mapping is None:
                gaps.append(f"{identity}: The original feature has no Rust mapping.")
                continue
            for owner in (feature, mapping):
                refs = owner.get("evidence", [])
                if not refs:
                    gaps.append(f"{identity}: The mapping lacks original evidence.")
                for reference in refs:
                    if reference not in bound or reference not in evidence:
                        raise ValueError(f"{identity}: An evidence reference is unresolved.")
                    if evidence[reference]["classification"] != "observed":
                        gaps.append(f"{identity}: Original evidence remains uncertain.")
            if not mapping.get("rust"):
                gaps.append(f"{identity}: The Rust component remains unmapped.")
            for name in mapping.get("rust", []):
                inputs[name] = hashlib.sha256(file(root, name).read_bytes()).hexdigest()
            dimensions = mapping["dimensions"]
            if set(dimensions) != DIMENSIONS:
                raise ValueError(f"{identity}: The mapping must cover all five dimensions.")
            for dimension, status in dimensions.items():
                if status not in {"matched", "different", "unknown", "unmapped", "untested", "user_exception"}:
                    raise ValueError("A parity dimension has an invalid result.")
                if status != "matched":
                    gaps.append(f"{identity}: {dimension} remains {status}.")
            if not mapping.get("tests"):
                gaps.append(f"{identity}: The feature has no test reference.")
            for test_id in mapping.get("tests", []):
                test = tests[test_id]
                if test["origin"] not in {"observed", "inferred", "proposed"} or not isinstance(test["expect"], dict) or not test["expect"]:
                    raise ValueError("A test needs a valid origin and exact expectations.")
                if not test.get("evidence") or any(name not in bound for name in test["evidence"]):
                    raise ValueError("A test has no bound original evidence.")
                if any(evidence[name]["classification"] != "observed" for name in test["evidence"]):
                    gaps.append(f"{identity}/{test_id}: The expected assertion remains uncertain.")
                if not test.get("scenarios"):
                    raise ValueError("A test must name an executed scenario.")
                for scenario in test["scenarios"]:
                    case = cases.get(scenario)
                    if case is None:
                        gaps.append(f"{identity}/{scenario}: The scenario has no executed capture.")
                        continue
                    if case.get("passed") is not True or case.get("differences") != []:
                        gaps.append(f"{identity}/{scenario}: The recorded comparison fails.")
                    for label in ("reference", "candidate"):
                        actual = case[label]
                        if actual.get("error") is not None or any(name not in actual or json.dumps(actual[name], sort_keys=True) != json.dumps(expected, sort_keys=True) for name, expected in test["expect"].items()):
                            gaps.append(f"{identity}/{scenario}/{label}: An exact expected assertion fails.")
        result["declared_original_features"] = len(original)
        result["selected_features"] = len(selected)
        if not gaps:
            result.update(status="passed", assessment="full_parity_gate_pass", full_parity_gate_pass=True)
        elif allow_partial:
            result.update(status="partial", assessment="incomplete")
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as error:
        result["errors"].append(str(error))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True)
    parser.add_argument("--matrix", default="verification/parity-matrix.json")
    parser.add_argument("--report", required=True)
    parser.add_argument("--allow-partial", action="store_true")
    args = parser.parse_args()
    result = check(args.project, args.matrix, args.allow_partial)
    path = Path(args.report)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] in {"passed", "partial"} and not result["errors"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
