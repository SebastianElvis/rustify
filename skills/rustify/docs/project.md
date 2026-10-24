# Project contract and state

The target project has three directories.

```text
PROJECT/
  recovered/
    contract.json
    state.json
    product.md
    ux.md
    architecture.md
    evidence.json
    evidence/
    scenarios.json
    tests.json
    roadmap.md
  implementation/
    Cargo.toml
    Cargo.lock
    src/
    tests/
  verification/
    checks.json
    comparison.json
    compatibility.md
    logs/
```

The external agent workspace holds `rust-design.md` and `plan.json`.
A project named `app` uses the sibling workspace `.app-rustify` by default.
The agent can select another external path with `init --work-dir WORK`.
The helper stores its absolute path in `recovered/state.json` as `work_dir`.
The helper rejects an internal workspace or a symlink.

## Contract

The agent writes `recovered/contract.json` with these fields.

| Field | Content |
| --- | --- |
| `target` | The executable, resources, version, platform, hash, and execution method. |
| `scope` | The supported workflows and interfaces. |
| `compatibility` | The required output, file, protocol, visual, and performance dimensions. |
| `environment` | The locale, clock, randomness, persistence, and service assumptions. |
| `exclusions` | The unsupported capabilities. |
| `budget` | The investigation limits and stopping conditions. |

## Checkpoints

| Phase | Required artifacts |
| --- | --- |
| `prepare` | `recovered/contract.json` |
| `discover` | The seven recovered model, evidence, scenario, test, and roadmap files shown above. |
| `plan` | External `rust-design.md` and `plan.json` |
| `implement` | `implementation/Cargo.toml`, `implementation/Cargo.lock`, Rust sources, and `verification/checks.json` |
| `validate` | `verification/comparison.json` and `verification/compatibility.md` |

The helper writes state atomically in `recovered/state.json`.
The helper checks phase order, nonempty required artifacts, JSON syntax, hashes, and executable identity.
The helper also hashes raw files in `recovered/evidence/`.
The helper hashes every implementation input except `target/` and `.git/` trees.
These inputs include resources, fixtures, empty files, and `.cargo` configuration.
The helper treats these inputs as opaque bytes.
The required JSON artifacts must still contain valid nonempty JSON.
The implementation checks must report `status: "passed"`.
Each required Cargo command must have a successful latest result.
The required commands are `cargo fmt`, `cargo clippy`, and `cargo test`.
The comparison must contain passing case records with consistent totals.
Each case must report `passed: true` and `differences: []`.
These checks verify report structure.
These checks do not prove that a command ran or that a capture is authentic.
Raw captures can be empty.
Evidence edits reopen discovery.
External plan edits reopen planning.
Rust source edits reopen implementation.
A different target requires a new project identity.
These structural gates do not certify semantic coverage.
The agent verifies artifact meaning before each checkpoint.

The agent runs `python3 <rustify>/scripts/project.py checkpoint PROJECT PHASE` for each phase.
The agent runs the helper with `status PROJECT` after an interruption.
Here, `<rustify>` means the installed skill folder.

## Evidence and scenarios

Each evidence record has `id`, `claim`, `classification`, `source`, and `limitations`.
The classification is `observed`, `inferred`, or `unknown`.
An observed claim links to a capture or exported REA evidence in `recovered/evidence/`.
An inferred claim links to observations and a falsifying experiment.
An unknown claim identifies missing evidence.
The agent keeps feature identifiers stable across records, scenarios, and tasks.
The agent labels creator intent and design rationale as inferences.
The agent labels proposed improvements and roadmap work separately from shipped behavior.

Each discovery worker returns separate evidence, scenarios, and test expectations.
The orchestrator merges them into the canonical files in `recovered/`.
CLI scenarios use the installed `rustify-validate` comparison format.
Other profiles use target-specific replay data.
The contract defines tolerances for variable results.
The agent does not normalize unexplained differences.

## Declarative tests

`recovered/tests.json` contains expectations, not executable test code.
Each record has an identifier, an origin, evidence identifiers, scenario references, and an `expect` object.
The origin is `observed`, `inferred`, or `proposed`.
The agent verifies each reference and its acceptance status.
The helper only checks nonempty valid JSON.

```json
[
  {
    "id": "TEST-001",
    "origin": "observed",
    "evidence": ["E-001"],
    "scenarios": ["encode-stdin"],
    "expect": {"returncode": 0, "stdout_b64": "YUdWc2JHOD0K", "stderr_b64": ""}
  }
]
```

Other profiles declare interaction, protocol, file, or state expectations in `expect`.
The implementation keeps executable tests under `implementation/tests/` and Rust source modules.
Verification keeps test results and captures under `verification/`.
