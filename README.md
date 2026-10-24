# Rustify

Rustify reconstructs local software from binary evidence in idiomatic Rust.
The output includes a product model, design specification, architecture, parity backlog, tests, and compatibility results.

![Rustify architecture](docs/architecture.svg)

## Install

The bundle follows the [Agent Skills format](https://github.com/vercel-labs/skills/blob/main/docs/creating-skills.md).
The instructions work with any host that loads that format.

```sh
npx skills add SebastianElvis/rustify --skill '*'
```

The repository is private. The installer requires Git access.
The full bundle requires all seven skills.
The user can ask the host agent to use `rustify` with a binary path and a compatibility goal.
The host uses its native skill invocation and task tools.

| Skill | Output |
| --- | --- |
| `rustify` | The skill prepares the target project and coordinates the phases. |
| `rustify-product` | The skill recovers workflows, rules, and proposed maintenance priorities. |
| `rustify-design` | The skill recovers interface behavior and design language. |
| `rustify-architecture` | The skill recovers technical components, data, and execution flows. |
| `rustify-plan` | The skill defines the Rust design, acceptance checks, and task dependencies. |
| `rustify-implement` | The skill builds complete Rust workflows and tests. |
| `rustify-validate` | The skill compares results and directs evidence-based repairs. |

The three discovery skills run in parallel when the host supports parallel tasks.
The host runs them sequentially otherwise.
[REA](https://github.com/morluto/rea) supplies the binary investigation backend.
The three discovery skills declare that dependency in their metadata.
The [REA setup guide](https://github.com/morluto/rea/blob/main/docs/installation.md) connects its tools to the selected agent.
The installed skill folders contain their runtime resources.
The target project stores generated files outside the installed bundle.
The target project contains `recovered/`, `implementation/`, and `verification/`.
The agent keeps temporary design and task plans in a separate workspace.

## Documentation

- [Product and vision](docs/product.md)
- [Architecture and LaTeX source](docs/architecture.md)
- [Evaluation method and dataset](docs/evaluation.md)
- [Target-project contract](skills/rustify/references/project.md)
- [Rust stack guide](skills/rustify-plan/references/rust-stack.md)

## Fidelity

The default contract requires faithful reconstruction.
Rustify maps original features, interactions, data, and components to the implementation.
Known differences remain parity gaps.
The evaluation dataset measures finite subsets and records unresolved differences.
Its passing checks do not establish full-product parity.

## Repository workflow

The default branch is `main`.
Every change uses a feature branch and a pull request.
GitHub allows squash merge only.
The author installs the local push guard with this command:

```sh
python3 scripts/install_hooks.py
```

The guard blocks direct pushes to `main` in this checkout.
The installer preserves existing hooks.
GitHub refused server-side branch protection for this private repository under the current plan.

## Checks

```sh
make test
make evaluate
make diagram
python3 scripts/check_install.py
```

The helper tests use Python's standard library.
The evaluations need Rust and the pinned reference binaries.
The first setup downloads release binaries and Cargo dependencies.
The fast evaluation then uses local inputs and a loopback HTTP server.
The reference binaries require macOS and the indicated CPU support.
The `b3sum` reference uses x86_64 and requires Rosetta on arm64.
The skill instructions themselves have no macOS requirement.

The default evaluation covers base64, BLAKE3, and HTTP.
The desktop evaluation needs a native GUI session for a fresh replay.
This command verifies the saved GUI captures and runs fresh Rust unit tests:

```sh
python3 scripts/evaluate.py --recorded-desktop
```

That command does not claim a fresh GUI replay.
Each track reports its scope and source-assisted repairs.
The results do not establish equivalence for every binary or input.
