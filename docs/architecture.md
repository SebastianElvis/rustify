# Rustify architecture

Rustify contains seven skills and three runtime Python helpers.
Host-native agents execute the installed instructions.
The installed skill bundle, temporary agent workspace, and generated target project have separate boundaries.

![Rustify architecture](architecture.svg)

## Components and evidence

| Component | Responsibility | Evidence |
| --- | --- | --- |
| `rustify` | The orchestrator prepares the contract, dispatches work, merges findings, and routes repairs. | `skills/rustify/SKILL.md` |
| `rustify-product` | The skill recovers capabilities and proposed maintenance work. | `skills/rustify-product/SKILL.md` |
| `rustify-design` | The skill recovers interface behavior and design language. | `skills/rustify-design/SKILL.md` |
| `rustify-architecture` | The skill recovers original components, boundaries, and workflow traces. | `skills/rustify-architecture/SKILL.md` |
| `rustify-plan` | The skill writes the temporary Rust design, decisions, tasks, and acceptance checks. | `skills/rustify-plan/SKILL.md` |
| `rustify-implement` | The skill implements complete workflows and runs Rust quality checks. | `skills/rustify-implement/SKILL.md` |
| `rustify-validate` | The skill compares behavior and reports measured compatibility. | `skills/rustify-validate/SKILL.md` |
| `project.py` | The helper checks phase order, target identity, artifact hashes, and freshness. | `skills/rustify/scripts/project.py` |
| `compare.py` | The helper captures and compares deterministic CLI runs. | `skills/rustify-validate/scripts/compare.py` |
| `parity.py` | The helper checks declared mappings, exact expectations, evidence hashes, and known gaps. | `skills/rustify-validate/scripts/parity.py` |
| REA | The external backend supplies investigation evidence for discovery. | `skills/rustify-architecture/SKILL.md` |
| Target project | The directory contains recovered/, implementation/, and verification/. | `skills/rustify/references/project.md` |

## Flow and boundaries

1. The original binary, resources, and scope contract enter `rustify`.
2. The orchestrator dispatches the three discovery skills in parallel when the host supports agents.
3. The orchestrator joins their findings and resolves contradictions before planning.
4. The plan, implementation, and validation skills run in order.
5. Validation differences reopen the affected discovery, planning, or implementation work.
6. The target project contains the reconstruction outputs throughout the workflow.

The host runs discovery sequentially when parallel agents are unavailable.
Workers have flexible task assignments and separate experiment data.
Workers coordinate access to shared REA sessions and application state.
Discovery exports required REA evidence into the target project.
REA remains an external investigation backend.
The host supplies agent execution and transport.

The target project has three folders.

| Folder | Contents |
| --- | --- |
| `recovered/` | `contract.json`, `state.json`, `product.md`, `ux.md`, `architecture.md`, `evidence.json`, `evidence/`, `scenarios.json`, `tests.json`, and `roadmap.md`. |
| `implementation/` | `Cargo.toml`, `Cargo.lock`, `src/`, and optional separate Rust tests in `tests/`. |
| `verification/` | `checks.json`, `comparison.json`, `compatibility.md`, and `logs/`. |

The architecture skill also produces editable diagrams and data models when original evidence requires them.
The validation skill records the original-to-Rust mapping in `verification/parity-matrix.json`.
The strict evidence gate writes `verification/parity.json`.
The full faithful contract cannot complete while that gate has errors or gaps.
The gate checks declared evidence consistency. The evaluator remains responsible for actual coverage.

The `recovered/tests.json` file stores declarative test specifications.
Each specification records an observed, inferred, or proposed origin.
The implementation contains executable code and tests.
Unit tests can reside in `src/`, and process E2E tests can use external replay files.

The agent workspace stores temporary `rust-design.md` and `plan.json` files outside the target project.
The plan skill writes these files.
The implementation skill reads the plan from that workspace.
The installed bundle contains reusable instructions and helpers.
Each skill keeps its router short.
References contain domain methods and output contracts.
Assets contain copyable specifications, plans, diagrams, and report templates.
The project helper checks structure and freshness.
The agent verifies evidence quality and semantic completeness.

The CLI helper compares stdout, stderr, status, and regular files.
Desktop, service, and game validation use target-specific host replay.
The helper's temporary directories separate data without providing OS-level containment.

## Figure files

The repository contains one architecture figure.
The editable source is [architecture.tex](architecture.tex).
The outputs are [architecture.pdf](architecture.pdf), [architecture.svg](architecture.svg), and [architecture.png](architecture.png).
The repository root supports this build command:

```sh
make diagram
```
