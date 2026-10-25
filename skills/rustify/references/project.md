# Project contract and state

## Fidelity contract

The agent copies `../assets/contract.json` into `recovered/contract.json`.
The agent replaces every `{{name}}` value with observed target data or an explicit user limit.
The agent records unavailable values as unknowns with a discovery task.
The default scope is `full_product`. The default compatibility mode is `faithful`.
The agent selects `subset` only when the user requests a bounded reconstruction or evaluation.
A subset records the user's words in `scope.user_instruction`.
Discovery skills read the scope from the contract and do not restate it.

| Field | Content |
| --- | --- |
| `target` | The executable, resources, platform, and SHA-256. |
| `scope` | The mode, the features, the unexplored surface, and the user instruction for a subset. |
| `compatibility` | The required product, behavior, UX, data, interface, and architecture fidelity. |
| `environment` | The locale, clock, randomness, persistence, and service assumptions. |
| `exclusions` | The unsupported capabilities. |
| `budget` | The investigation limits and stopping conditions. |

## Target project

```text
PROJECT/
  recovered/
    contract.json  state.json  model.json
    product.md  ux.md  architecture.md  roadmap.md
    evidence.json  evidence/  scenarios.json  tests.json
  implementation/
    Cargo.toml  Cargo.lock  src/  tests/
    docs/design.md  docs/adr/
  verification/
    checks.json  comparison.json  parity.json  compatibility.md  logs/
```

The agent workspace stays outside the project.
A project named `app` uses the sibling workspace `.app-rustify` by default.
The agent can select another external path with `init --work-dir WORK`.
The helper rejects an internal workspace or a symlink.

## Ledger

`recovered/model.json` is the single traceability record.
The agent starts from [the ledger asset](../assets/model.json).
Documents describe the ledger items. They do not keep a second copy of a mapping.

| Section | Owner | Content |
| --- | --- | --- |
| `inventory` | Discovery | The inventory completeness flag and its evidence basis. |
| `requirements` | Discovery | EARS requirements with the attributes in [the standards guide](standards.md). |
| `components` | Architecture discovery | C4 containers and components. |
| `edges` | Architecture discovery | Control, data, and static relations between components. |
| `correspondences` | Planning | One Rust source file for each original component. |
| `slices` | Planning | The walking skeleton and the later slices. |
| `exceptions` | Planning | User-authorized differences with the quoted user instruction. |
| `gaps` | All phases | Open and closed gaps with their items and closure checks. |

Each identifier stays stable across the ledger, documents, scenarios, and tests.
The parity gate derives each requirement result from evidence and comparisons.
No agent writes a `passed` status into the ledger.

## Evidence and scenarios

Each evidence record has `id`, `claim`, `classification`, `source`, and `limitations`.
The classification is `observed`, `inferred`, or `unknown`.
An observed record also has `path` and `sha256` for its capture in `recovered/evidence/`.
An inferred record links to observations and a falsifying experiment.
An unknown record identifies missing evidence.
The agent labels creator intent and design rationale as inferences.

CLI scenarios use the `rustify-validate` comparison format.
Other profiles use target-specific replay data with the same report fields.
The contract defines tolerances for variable results.
The agent does not normalize unexplained differences.

## Declarative tests

`recovered/tests.json` contains expectations, not executable test code.
Each record has `id`, `origin`, `evidence`, `scenarios`, and `expect`.
The origin is `observed`, `inferred`, or `proposed`.

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

The implementation keeps executable tests under `implementation/tests/` and Rust source modules.

## Checkpoints

| Phase | Required artifacts |
| --- | --- |
| `prepare` | `recovered/contract.json` |
| `discover` | The recovered documents, evidence, scenarios, tests, and the discovery sections of `model.json`. |
| `plan` | The planning sections of `model.json` and `implementation/docs/design.md`. |
| `implement` | The Cargo files, the Rust sources, and a `checks.json` from the helper's `check` command. |
| `validate` | `comparison.json`, `parity.json`, and `compatibility.md`. |

```sh
python3 <rustify>/scripts/project.py check PROJECT [--deny] [--mutants]
python3 <rustify>/scripts/project.py checkpoint PROJECT PHASE
python3 <rustify>/scripts/project.py status PROJECT
```

The helper writes state atomically in `recovered/state.json`.
The helper hashes each required artifact. It hashes only the owned sections of `model.json`.
A change to a section reopens the phase that owns it.
The `plan` checkpoint requires one walking skeleton, an acyclic slice graph, and a slice for each scoped requirement.
The `check` command runs `cargo fmt`, `cargo clippy`, and `cargo test` and records the logs and their hashes.
The `--deny` option adds `cargo deny check`. The `--mutants` option adds `cargo mutants` and records the mutation score.
The `implement` checkpoint accepts the checks only for the current implementation bytes.
The `validate` checkpoint requires `full_parity_pass` for the full product or `scoped_pass` for a subset.
These gates check structure, integrity, and recorded results.
They do not certify semantic coverage. The agent verifies artifact meaning before each checkpoint.
