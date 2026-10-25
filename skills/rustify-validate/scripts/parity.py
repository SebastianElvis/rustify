#!/usr/bin/env python3
"""The gate derives parity results from the ledger, the evidence, and recorded comparisons."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re


DIMENSIONS = {"product", "ux", "data", "behavior"}
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


def read(root, name, inputs, parse=True):
    data = file(root, name).read_bytes()
    inputs[name] = hashlib.sha256(data).hexdigest()
    return json.loads(data) if parse else data.decode(errors="replace")


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
    edges = records(model["edges"])
    for edge in edges.values():
        if edge["source"] not in components or edge["target"] not in components or edge["kind"] not in {"control", "data", "static"}:
            raise ValueError(f"The edge has an invalid component or kind: {edge['id']}")
    expected = {}
    for edge in edges.values():
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


def check(project, comparisons=("verification/comparison.json",), allow_partial=False):
    root = Path(project).resolve()
    result = {"status": "failed", "assessment": "incomplete", "full_parity_gate_pass": False, "semantic_truth_verified": False, "inputs": {}, "errors": [], "gaps": []}
    try:
        inputs = result["inputs"]
        contract = read(root, "recovered/contract.json", inputs)
        model = read(root, "recovered/model.json", inputs)
        evidence = records(read(root, "recovered/evidence.json", inputs))
        tests = records(read(root, "recovered/tests.json", inputs))
        target = result["target_sha256"] = contract["target"]["sha256"]
        if not isinstance(target, str) or not re.fullmatch(r"[0-9a-f]{64}", target):
            raise ValueError("The original identity must be a lowercase SHA-256 value.")
        scope = contract["scope"]
        if scope["mode"] not in {"full_product", "subset"}:
            raise ValueError("The scope must identify the full product or a subset.")
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
        exceptions = records(model["exceptions"])
        edges = records(model["edges"])
        scoped_items = {name for item in requirements.values() if item.get("in_scope", True) for name in item["components"]}
        scoped_items |= {edge["id"] for edge in edges.values() if {edge["source"], edge["target"]} & scoped_items}
        excepted = {item for value in exceptions.values() if value.get("user_instruction") for item in value["items"]}
        gaps = []
        used = set()
        open_gaps = {}
        for gap in records(model["gaps"]).values():
            if gap["status"] == "open":
                for item in gap["items"]:
                    open_gaps.setdefault(item, []).append(gap["id"])

        def bound(reference, owner):
            if reference not in evidence:
                raise ValueError(f"{owner}: An evidence reference is unresolved.")
            return evidence[reference]["classification"] == "observed"

        for item in components.values():
            if item["level"] not in {"container", "component"} or item["classification"] not in CLASSES:
                raise ValueError(f"The component has an invalid level or classification: {item['id']}")
            if item["classification"] != "observed" or not all(bound(name, item["id"]) for name in item["evidence"]):
                gaps.append((item["id"], item["id"] in scoped_items, f"{item['id']}: The component remains uncertain."))
        structure = result["reflexion"] = reflexion(root, model, components, inputs)
        for kind in ("absences", "divergences", "merged", "unmapped", "extra_modules"):
            for item in structure[kind]:
                if item in excepted:
                    used.add(item)
                else:
                    gaps.append((item, item in scoped_items or kind in {"divergences", "merged", "extra_modules"}, f"{item}: The reflexion check reports {kind.replace('_', ' ')}."))
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
            reasons += [f"The gap {name} remains open." for name in open_gaps.get(identity, [])]
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
                        if actual.get("error") is not None or any(name not in actual or json.dumps(actual[name], sort_keys=True) != json.dumps(value, sort_keys=True) for name, value in test["expect"].items()):
                            reasons.append(f"{scenario}/{label}: An exact expected assertion fails.")
                            mismatch = mismatch or label == "candidate"
                    if case.get("passed") is not True:
                        reasons.append(f"{scenario}: The recorded comparison fails.")
                        mismatch = True
            statuses[identity] = "passed" if not reasons else "exception" if identity in excepted else "failed" if mismatch else "incomplete"
            if statuses[identity] == "exception":
                used.add(identity)
            else:
                gaps += [(identity, item.get("in_scope", True), f"{identity}: {reason}") for reason in reasons]
            if not item.get("in_scope", True):
                gaps.append((identity, False, f"{identity}: The requirement is outside the authorized subset."))
        for kind, names in DOCUMENTS:
            text = "".join(read(root, name, inputs, False) for name in names)
            gaps += [(identity, True, f"{identity}: {' or '.join(names)} does not name this item.") for identity in (requirements if kind == "requirements" else components) if not re.search(rf"\b{re.escape(identity)}\b", text)]
        roadmap = read(root, "recovered/roadmap.md", inputs, False)
        gaps += [(name, True, f"{name}: recovered/roadmap.md does not name this open gap.") for names in open_gaps.values() for name in names if name not in roadmap]
        if model["inventory"]["complete"] is not True:
            gaps.append(("inventory", False, "The original inventory remains incomplete."))
        if scope["mode"] == "subset" and not scope.get("user_instruction"):
            gaps.append(("scope", True, "The subset has no recorded user instruction."))
        if scope["mode"] == "full_product" and any(not item.get("in_scope", True) for item in requirements.values()):
            gaps.append(("scope", True, "The full-product contract cannot exclude a requirement."))
        result["gaps"] = sorted({message for _, _, message in gaps})
        result["requirements"] = statuses
        result["slices"] = {item["id"]: all(statuses.get(name) == "passed" for name in item["requirements"]) for item in model["slices"]}
        result["dimensions"] = {name: {status: sum(requirements[key]["dimension"] == name and value == status for key, value in statuses.items()) for status in ("passed", "failed", "incomplete", "exception")} for name in sorted(DIMENSIONS)}
        result["exceptions_used"] = sorted(used)
        scoped = not any(in_scope for _, in_scope, _ in gaps) and all(statuses[key] in {"passed", "exception"} for key, item in requirements.items() if item.get("in_scope", True))
        if not gaps and not result["exceptions_used"] and scope["mode"] == "full_product":
            result.update(status="passed", assessment="full_parity_pass", full_parity_gate_pass=True)
        elif "failed" in statuses.values():
            result["assessment"] = "failed"
        elif scoped and scope["mode"] == "subset":
            result.update(status="passed", assessment="scoped_pass")
        if result["status"] != "passed" and allow_partial:
            result["status"] = "partial"
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as error:
        result["errors"].append(str(error))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True)
    parser.add_argument("--comparison", action="append")
    parser.add_argument("--report", required=True)
    parser.add_argument("--allow-partial", action="store_true")
    args = parser.parse_args()
    result = check(args.project, args.comparison or ["verification/comparison.json"], args.allow_partial)
    path = Path(args.report)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({key: result[key] for key in ("status", "assessment", "errors")} | {"gaps": len(result["gaps"])}, indent=2))
    return 0 if result["status"] in {"passed", "partial"} and not result["errors"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
