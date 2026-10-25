# Project format and state

## Fidelity rule

Rustify always reconstructs the full product with one-to-one compatibility.
The helper `init` command records the target path and SHA-256 in `recovered/state.yaml`.
`recovered/product.md` records the target identity, resources, platform, and environment.
The environment covers the locale, clock, randomness, persistence, and services.
`recovered/roadmap.md` records the investigation limits and stopping conditions.
A missing feature is an open gap. The agent keeps working on each open gap.

## Target project

```text
PROJECT/
  recovered/
    state.yaml  model.yaml
    product.md  ux.md  architecture.md  roadmap.md
    evidence.yaml  evidence/  scenarios.yaml  tests.yaml
  implementation/
    Cargo.toml  Cargo.lock  src/  tests/
    docs/design.md  docs/adr/
  verification/
    checks.yaml  comparison.yaml  parity.yaml  compatibility.md  logs/
```

The agent workspace stays outside the project.
A project named `app` uses the sibling workspace `.app-rustify` by default.
The agent can select another external path with `init --work-dir WORK`.
The helper rejects an internal workspace or a symlink.
The agent uses YAML for authored structured records, captures, test fixtures, and freeze manifests.
The agent keeps prose in Markdown.
The agent preserves external formats, such as Cargo messages, REA exports, and original product files.

## Ledger

`recovered/model.yaml` is the single traceability record.
The agent starts from [the ledger asset](../assets/model.yaml).
Documents describe the ledger items. They do not keep a second copy of a mapping.

| Section | Owner | Content |
| --- | --- | --- |
| `inventory` | Discovery | The inventory completeness flag. `recovered/product.md` names its evidence basis. |
| `requirements` | Discovery | EARS requirements with the attributes in [the standards guide](standards.md). |
| `surface` | Discovery | Each user-visible option, program name, environment variable, diagnostic, input partition, condition, state, and interface item, with the requirements that cover it. |
| `components` | Architecture discovery | C4 containers and components. |
| `edges` | Architecture discovery | Control, data, and static relations between components. |
| `correspondences` | Planning | One Rust source file for each original component. |
| `slices` | Planning | The walking skeleton and the later slices. |
| `gaps` | All phases | The `id`, the `items`, and the `open` or `closed` status. `recovered/roadmap.md` gives the kind and the closure check. |

Each identifier stays stable across the ledger, documents, scenarios, and tests.
The parity gate derives each requirement result from evidence and comparisons.
No agent writes a `passed` status into the ledger.

## Evidence and scenarios

Each evidence record in `recovered/evidence.yaml` has `id` and `classification`.
The classification is `observed`, `inferred`, or `unknown`.
An observed record also has `path` and `sha256` for its capture in `recovered/evidence/`.
The documents that cite an evidence ID state its claim, source, and limitations.
The citation of an inferred record names its observations and a falsifying experiment.
The citation of an unknown record names the missing evidence.
The agent labels creator intent and design rationale as inferences.

CLI scenarios use the `rustify-validate` comparison format.
Other profiles use target-specific replay data with the same report fields.
The compatibility constraints in `recovered/product.md` define tolerances for variable results.
The agent does not normalize unexplained differences.

## Declarative tests

`recovered/tests.yaml` contains expectations, not executable test code.
Each record has `id`, `origin`, `evidence`, `scenarios`, and `expect`.
The origin is `observed`, `inferred`, or `proposed`.

```yaml
- id: TEST-001
  origin: observed
  evidence: [E-001]
  scenarios: [encode-stdin]
  expect: {returncode: 0, stdout_b64: YUdWc2JHOD0K, stderr_b64: ''}
```

The implementation keeps executable tests under `implementation/tests/` and Rust source modules.

## Checkpoints

| Phase | Required artifacts |
| --- | --- |
| `discover` | The recovered documents, evidence, scenarios, tests, and the discovery sections of `model.yaml`. |
| `plan` | The planning sections of `model.yaml` and `implementation/docs/design.md`. |
| `implement` | The Cargo files, the Rust sources, and a `checks.yaml` from the helper's `check` command. |
| `validate` | `comparison.yaml`, `parity.yaml`, and `compatibility.md`. |

```sh
python3 <rustify>/scripts/project.py check PROJECT [--deny] [--mutants]
python3 <rustify>/scripts/project.py checkpoint PROJECT PHASE
python3 <rustify>/scripts/project.py status PROJECT
```

The helper writes state atomically in `recovered/state.yaml`.
The helper hashes each required artifact. It hashes only the owned sections of `model.yaml`.
A change to a section reopens the phase that owns it.
The `plan` checkpoint requires one walking skeleton, an acyclic slice graph, and a slice for each requirement.
The `check` command runs `cargo fmt`, `cargo clippy`, and `cargo test` and records the logs and their hashes.
The `--deny` option adds `cargo deny check`. The `--mutants` option adds `cargo mutants` and records the mutation score.
The `implement` checkpoint accepts the checks only for the current implementation bytes.
The `validate` checkpoint requires `full_parity_pass`.
These gates check structure, integrity, and recorded results.
They do not certify semantic coverage. The agent verifies artifact meaning before each checkpoint.
