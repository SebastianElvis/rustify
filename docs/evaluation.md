# Evaluation

Rustify evaluates a reconstruction against an identified original binary.
The report separates measured behavior from unexplored behavior.
The default reconstruction requires one-to-one product, UX, component, data, and behavior mappings.
The compact dataset measures explicit subsets.
A passing subset does not establish full-product parity.

## Complete flow

1. The evaluator selects an open-source target with a released binary and test vectors.
2. The evaluator records the binary origin, version, platform, license, and SHA-256.
3. The reconstruction receives only the binary, resources, skill, and execution environment.
4. Discovery captures product, experience, architecture, and reproducible scenarios.
5. Planning defines scope and acceptance checks before implementation.
6. The reconstruction implements idiomatic Rust with unit and E2E tests.
7. The evaluator freezes the Rust source hash and discovery artifacts.
8. A separate evaluation pass adds challenge cases.
9. The evaluator reveals the original source and upstream vectors.
10. The evaluator compares product coverage, architecture recovery, and behavior separately.
11. A failure preserves a reproducer. A repair repeats the affected checks.
12. The final report states source access, repairs, measured coverage, and remaining gaps.

The target project separates `recovered/`, `implementation/`, and `verification/`.
The agent keeps temporary design and task plans outside the target project.
The recovered test specifications record observable expectations and their origin.
The verification folder records execution results.

The source audit must not quietly become a source translation pass.
The evaluator records source-assisted changes separately if they become necessary.
The evaluator does not claim perfect isolation when one agent performs both passes.

## CLI comparison

Each scenario contains these fields:

```json
[
  {
    "id": "encode-stdin",
    "args": ["-w", "0"],
    "stdin_b64": "aGVsbG8=",
    "files": {}
  }
]
```

The `stdin_b64` and file values encode raw bytes.
Optional `env` entries configure uncontrolled variables.
The helper reserves locale, timezone, home, and path variables.

```sh
python3 skills/rustify-validate/scripts/compare.py --reference /path/to/original --candidate /path/to/implementation --cases PROJECT/recovered/scenarios.json --report PROJECT/verification/comparison.json --name base64
```

The helper runs each program in a separate temporary directory.
The helper sets the same argument-zero name and deterministic environment.
The helper compares stdout, stderr, exit status, and resulting regular files.
The report preserves inputs, raw byte captures, and executable hashes.
The helper fails on time limits and execution errors even when both programs fail alike.
The POSIX helper does not provide OS-level containment for hostile binaries.
Other hosts use an equivalent target-specific replay tool.

## Compact dataset

| Track | Reference | Scope |
| --- | --- | --- |
| CLI | GNU base64 9.12 | Encoding, decoding, wrapping, files, options, and error behavior. |
| Cryptography | b3sum 1.8.7 | Hashing, keyed hashing, derivation, XOF output, and checksum verification. |
| Client | xh 0.26.3 | Local HTTP methods, headers, bodies, redirects, and error status. |
| Desktop | zenity 0.10.15 | Entry acceptance, entry cancellation, question choices, and information acknowledgement. |

Each evaluation wrapper has a `run.py` outside its generated `target/`.
The target directory follows the three-folder product layout.
The wrapper can keep historical agent fixtures outside that directory.
The original source remains hidden until a recorded source and model freeze.
Archives preserve the original files when later audits require source-assisted repairs.
The cryptography, client, and desktop tracks disclose these repairs.
The base64 implementation needs no source-assisted repair.

The default replay runs CLI, cryptography, and client checks.
The desktop option checks recorded GUI evidence and fresh Rust unit tests.
The desktop report states that it does not perform a fresh native replay.
The desktop runner rejects captures from an earlier implementation.
The initial desktop investigation uses actual native controls and process captures.
The desktop source audit maps its scenarios to upstream interactive tests.
The audit does not claim that the upstream interactive suite ran.

```sh
make evaluate
python3 scripts/evaluate.py --recorded-desktop
```

The first setup needs internet access for pinned binaries and Cargo dependencies.
Subsequent replay uses local inputs and loopback HTTP.
The dataset requires macOS and the reference binaries' CPU support.
The skill bundle remains host-neutral.

## Evaluation checks

- The original passes a repeatability comparison against itself.
- Unit tests verify encoding logic, partial results, and boundary conditions.
- E2E cases verify command parsing, input files, and errors.
- Challenge cases exercise malformed and generated inputs.
- Upstream vectors run against both executables after the source reveal.
- A deliberately wrong implementation fails the comparison.
- Resume tests detect changes to inputs and Rust source.

## Scores

| Dimension | Evidence |
| --- | --- |
| Product coverage | The feature inventory maps to source-defined capabilities and tests. |
| Experience coverage | Recovered interface states map to observed commands or interactions. |
| Architecture recovery | Recovered components and flows map to source components. |
| Behavioral compatibility | Exact comparisons pass for the declared scenario set. |
| Rust quality | Formatting, lint, unit, and E2E checks pass. |
| Evidence quality | Each conclusion has an origin and a stated limitation. |

The architecture assessment maps original components to Rust components.
Each mapping preserves responsibilities, interfaces, state ownership, and execution boundaries where evidence permits them.
The report keeps unknown and different mappings open.
Each track stores its report in `evaluations/<track>/target/verification/compatibility.md`.

## Strict parity gate

The full-product workflow records its inventory and mappings in `verification/parity-matrix.json`.
The validation skill provides the matrix asset and its field definitions.
The checker rejects known gaps, incomplete inventories, differing dimensions, and stale inputs.
The checker verifies recorded assertions against both original and Rust captures.
The checker records its result in `verification/parity.json`.
A passing machine gate does not prove that the declared inventory covers every original feature.
The agent must justify that inventory with evidence.

```sh
python3 skills/rustify-validate/scripts/parity.py --project PROJECT --report PROJECT/verification/parity.json
```
