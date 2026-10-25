# Rustify

**Closed source should not block reconstruction.**

Rustify gives AI agents a workflow to reconstruct software from a binary in idiomatic Rust.
It recovers product specifications, UX, architecture, evidence, and tests alongside the implementation.
The goal is software that you can inspect, build, and maintain without the original source.

## Installation

Your environment needs Node.js 22.20 or later, Python 3, and a Rust toolchain with Cargo.

```sh
npx skills add SebastianElvis/rustify --skill '*'
```

The [Skills CLI](https://github.com/vercel-labs/skills/blob/main/docs/commands.md) installs all seven skills and lets you select your agents.
The installation applies to the current project by default.
The `-g` option installs the bundle across your projects.

Rustify follows the [Agent Skills format](https://agentskills.io/specification).
The bundle works with compatible agents such as Claude Code, Codex, Cursor, and OpenCode.
The CLI lists its [supported agents](https://github.com/vercel-labs/skills/blob/main/docs/agents.md).
Local and cloud agents use the same skill files.
Their environment must provide the target binary, its resources, and a compatible runtime.
Desktop investigation also needs a GUI session.

[REA](https://github.com/morluto/rea) supplies the reverse-engineering tools.
Its [installation guide](https://github.com/morluto/rea/blob/main/docs/installation.md) explains how to connect those tools to your agent.
The three discovery skills declare REA as a dependency.
The skill installer does not configure REA automatically.

## Usage

You give your agent the binary path, its resources, and an output folder.
You invoke the main `rustify` skill through your agent's skill interface or a prompt:

```text
Use the rustify skill to reconstruct /path/to/program in Rust.
Write the target project to ./reconstructed-program.
Preserve the original features, behavior, UX, data, and component boundaries.
Recover the product and architecture documents with supporting evidence.
Run unit tests and E2E comparisons against the original.
Keep every known mismatch open until a repair resolves it.
```

The default contract covers the full product.
You can request a bounded evaluation in your prompt.
The agent saves checkpoints and reopens affected phases when inputs change.

### Output

The target project contains three folders:

| Folder | Contents |
| --- | --- |
| `recovered/` | Product and UX specifications, architecture, diagrams, data models, contract, state, evidence, declarative tests, and a parity backlog. |
| `implementation/` | The Rust project, dependencies, source, and executable tests. |
| `verification/` | Check results, original-to-Rust comparisons, parity assessments, reports, and logs. |

The agent produces diagrams and data models when the evidence supports them.
Temporary Rust design and task plans stay in a separate agent workspace.
The [project contract](skills/rustify/references/project.md) defines the output formats.

## Workflow

![Rustify architecture](docs/architecture.svg)

1. **Preparation:** `rustify` records the target, environment, and compatibility contract.
2. **Discovery:** `rustify-product`, `rustify-design`, and `rustify-architecture` collect evidence in parallel when the agent supports parallel work.
3. **Planning:** `rustify-plan` maps original components to Rust components and defines acceptance checks.
4. **Implementation:** `rustify-implement` builds complete workflows and runs Rust quality checks.
5. **Validation:** `rustify-validate` compares both versions and returns defects to the affected phase.

The agent runs discovery tasks sequentially when parallel execution is unavailable.
The [architecture guide](docs/architecture.md) includes the diagram's editable LaTeX source.

## Design principles

- **The original defines the product.** Rustify targets one-to-one mappings wherever evidence permits them. A convenient redesign does not close a parity gap.
- **Evidence outranks guesses.** Findings separate observations, inferences, and unknowns.
- **Tests must challenge the reconstruction.** Unit tests, E2E comparisons, independent expectations, and upstream vectors check different failure modes.
- **Rust code follows Rust conventions.** The implementation preserves original responsibilities and execution boundaries. The [stack guide](skills/rustify-plan/references/rust-stack.md) ties dependencies to those requirements.
- **Reports keep gaps visible.** A passing subset does not establish full-product parity. Changed evidence invalidates stale results.

## Development and evaluation

Contributors run these checks from the repository root:

```sh
make test
make evaluate
python3 scripts/check_install.py
```

The compact dataset covers GNU base64, BLAKE3 hashing, an HTTP client, and native desktop dialogs.
The default evaluation runs the first three tracks.
The desktop option verifies saved GUI captures and runs fresh Rust tests:

```sh
python3 scripts/evaluate.py --recorded-desktop
```

The evaluation fixtures require macOS.
These fixture requirements do not restrict the skill bundle to macOS.
The [evaluation guide](docs/evaluation.md) records scopes, source-assisted repairs, and reproduction details.

Contributors rebuild the architecture figure with `make diagram`.
The build needs LaTeX, latexmk, and Poppler.
Each skill keeps its main instructions short and stores supporting methods, templates, and helpers in its resource folders.

## Documentation

- [Product and vision](docs/product.md)
- [Architecture and diagram source](docs/architecture.md)
- [Evaluation method and dataset](docs/evaluation.md)
- [Target-project contract](skills/rustify/references/project.md)
- [Rust stack guide](skills/rustify-plan/references/rust-stack.md)

## License

Rustify uses the [GNU General Public License v3.0](LICENSE).
