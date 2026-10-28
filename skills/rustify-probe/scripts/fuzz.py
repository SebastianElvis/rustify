#!/usr/bin/env python3
"""Search for inputs that make the original and the Rust implementation differ."""

import argparse
import base64
import copy
import hashlib
from pathlib import Path
import random

import yaml

import compare


def mutate(case, corpus, rng):
    case = copy.deepcopy(case)
    data = bytearray(compare.decode(case.get("stdin_b64", "")))
    position = rng.randrange(len(data) + 1)
    choice = rng.randrange(5)
    if choice == 0 and data:
        data[position % len(data)] ^= 1 << rng.randrange(8)
    elif choice == 1:
        data[position:position] = bytes([rng.randrange(256)])
    elif choice == 2 and data:
        del data[position:position + rng.randrange(1, 8)]
    elif choice == 3:
        other = compare.decode(rng.choice(corpus).get("stdin_b64", ""))
        data = data[:position] + other[rng.randrange(len(other) + 1):]
    else:
        pool = [value for item in corpus for value in item["args"]]
        args = case["args"]
        if args and rng.randrange(2):
            del args[rng.randrange(len(args))]
        elif pool:
            args.insert(rng.randrange(len(args) + 1), rng.choice(pool))
    case["stdin_b64"] = base64.b64encode(bytes(data)).decode("ascii")
    return case


def fuzz(reference, candidate, seeds, iterations=200, seed=0, name=None, timeout=5):
    compare.validate(seeds)
    rng, name = random.Random(seed), Path(reference).name if name is None else name
    paths = {"reference": Path(reference).resolve(strict=True), "candidate": Path(candidate).resolve(strict=True)}
    corpus, classes, divergences, errors = list(seeds), set(), [], []
    for index in range(iterations):
        case = rng.choice(corpus)
        for _ in range(rng.randrange(1, 9)):
            case = mutate(case, corpus, rng)
        case["id"] = f"fuzz-{seed}-{index}"
        results = {label: compare.run(path, name, case, timeout) for label, path in paths.items()}
        differences = compare.differ(results)
        if differences:
            (errors if "execution_error" in differences else divergences).append({"input": case, **results, "differences": differences})
        behavior = tuple((result["returncode"], hashlib.sha256(compare.decode(result["stderr_b64"])).hexdigest()) for result in results.values())
        if behavior not in classes:
            classes.add(behavior)
            corpus.append(case)
    return {
        "status": "invalid" if errors or iterations <= 0 else "failed" if divergences else "passed", "iterations": iterations, "seed": seed, "program_name": name,
        "behavior_classes": len(classes), "corpus": len(corpus), "divergences": divergences, "errors": errors,
        "executables": {label: {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()} for label, path in paths.items()},
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference", required=True)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--seeds", required=True)
    parser.add_argument("--report", required=True)
    parser.add_argument("--iterations", type=int, default=200)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--timeout", type=float, default=5)
    parser.add_argument("--name", help="The default is the original filename.")
    args = parser.parse_args()
    report = fuzz(args.reference, args.candidate, yaml.safe_load(Path(args.seeds).read_text()), args.iterations, args.seed, args.name, args.timeout)
    destination = Path(args.report)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(yaml.safe_dump(report, sort_keys=False))
    print(yaml.safe_dump({key: report[key] for key in ("status", "iterations", "behavior_classes")} | {"divergences": len(report["divergences"]), "errors": len(report["errors"])}, sort_keys=False), end="")
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
