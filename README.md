# Rustify

**Closed source should not block reconstruction.**

Rustify gives AI agents a workflow to reconstruct software from a binary in idiomatic Rust.
It recovers product specifications, UX, architecture, evidence, and tests alongside the implementation.
Rustify depends on [REA](https://github.com/morluto/rea) for reverse engineering.
The goal is software that you can inspect, build, and maintain without the original source.

## Installation

The setup below uses Node.js 24.x (24.22.1 or later), npm, Python 3.11 or later with PyYAML, and Rust with Cargo.
The Rustify helpers read and write YAML with PyYAML.
You install it with `python3 -m pip install pyyaml`.

### 1. Set up REA

REA supplies binary analysis and runtime evidence through `rustify-probe`.

```sh
npx rea-agents setup
```

You select the agents that will use REA.
You review the proposed configuration and approve the changes.
Setup registers the MCP server and installs REA's matching workflow instructions.
You restart the agents named in the completion message.

Native decompilation uses Hopper, Ghidra, or IDA.
Setup can connect an existing Hopper or Ghidra installation.
It can also install Hopper when you select that option.
Other target types can use REA's built-in inspection tools.
The [REA setup reference](https://github.com/morluto/rea/blob/main/docs/installation.md) provides additional provider settings and troubleshooting steps.

### 2. Install Rustify

You run this command from your project folder:

```sh
npx skills add SebastianElvis/rustify --skill '*'
```

The [Skills CLI](https://github.com/vercel-labs/skills) installs all eight Rustify skills and prompts you to select your agents.
The installation applies to the current project.
The `-g` option makes the bundle available across your projects:

```sh
npx skills add SebastianElvis/rustify --skill '*' -g
```

Rustify follows the [Agent Skills format](https://agentskills.io/specification).
[Compatible agents](https://github.com/vercel-labs/skills/blob/main/docs/agents.md) include Claude Code, Codex, Cursor, and OpenCode.
Local and cloud agents use the same skill files.
Their environment must provide REA, the target binary, its resources, and a compatible runtime.
Desktop investigation also needs a GUI session.

### 3. Check the setup

This command checks the installed REA workflow:

```sh
npx rea-agents doctor --skill --json
```

Native analysis also needs a working provider.
This example checks Hopper:

```sh
npx rea-agents doctor --provider hopper --json
```

You can replace `hopper` with `ghidra` or `ida` for your configured provider.
Your agent must have access to REA through MCP or the CLI.

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

Rustify always reconstructs the full product.
A missing feature stays an open gap until the agent completes it.
The agent saves checkpoints and reopens affected phases when inputs change.

### Output

The target project contains three folders:

| Folder | Contents |
| --- | --- |
| `recovered/` | The traceability ledger, product and UX specifications, architecture, diagrams, data models, state, evidence, declarative tests, and a parity backlog. |
| `implementation/` | The Rust project, dependencies, source, executable tests, the Rust design, and decision records. |
| `verification/` | Executed check results, original-to-Rust comparisons, fuzz reports, the parity gate result, the assurance case, and logs. |

The ledger `recovered/model.yaml` links each EARS requirement to evidence, tests, components, Rust modules, slices, and gaps.
The agent produces diagrams and data models when the evidence supports them.
The [project format](skills/rustify/references/project.md) defines the output formats.
The [standards guide](skills/rustify/references/standards.md) defines the writing rules, the terminology, and the requirement and architecture forms.

## Workflow

![Rustify architecture](docs/architecture.svg)

1. **Preparation:** `rustify` records the target identity and the checkpoint state.
2. **Characterization:** `rustify-probe` captures the first scenarios and relevant binary evidence through REA.
3. **Discovery:** `rustify-product`, `rustify-design`, and `rustify-architecture` write EARS requirements, C4 components, and evidence in parallel when the agent supports parallel work.
4. **Planning:** `rustify-plan` maps each original component to one Rust module and plans a walking skeleton and risk-ordered slices.
5. **Slices:** `rustify-implement` builds one slice at a time with acceptance tests first. `rustify-validate` checks each slice before the next one.
6. **Acceptance:** `rustify-validate` requests fresh probes, runs the reflexion check and parity gate, and writes an assurance case.

The discovery, planning, implementation, and validation skills use `rustify-probe` for shared captures and execution traces.
The agent runs discovery tasks sequentially when parallel execution is unavailable.
The [architecture guide](docs/architecture.md) includes the diagram's editable LaTeX source.

## Design principles

- **We strive for one-to-one mapping.** Rustify maps the original product, UX, behavior, data, and architecture to the Rust implementation. Known differences remain open until a repair resolves them.
- **Evidence and user experience guide reconstruction.** Observed workflows, interface states, binary evidence, and tests support each mapping. Unit tests, E2E comparisons, independent expectations, and available upstream vectors challenge the result.
- **Rust code follows Rust conventions.** The implementation preserves original responsibilities and execution boundaries. The [stack guide](skills/rustify-plan/references/rust-stack.md) ties dependencies to those requirements.
- **Reports keep gaps visible.** Only a full-product pass establishes parity. Changed evidence invalidates stale results.
- **Standards keep agents consistent.** Requirements follow ISO/IEC/IEEE 29148 and EARS. Architecture follows ISO/IEC/IEEE 42010, C4, and arc42. Prose follows ASD-STE100.

## Development and evaluation

Contributors run these checks from the repository root:

```sh
make test
make evaluate
python3 scripts/check_install.py
```

The dataset covers GNU base64, BLAKE3 hashing, an HTTP client, native desktop dialogs, bzip2, Lua, SQLite, Ninja, and Doom.
The last five tracks use hardened `-O3`, LTO, and stripped reference builds.
The [evaluation overview](evaluations/README.md) explains the track selection.
The repository stores the pinned references, cases, and scorers, not agent outputs.
You reconstruct each reference into `work/projects/<track>` with your agent.
`make evaluate` scores the first three tracks.
The `--desktop` option also scores saved GUI captures:

```sh
python3 scripts/evaluate.py --desktop
```

The agent evaluation runs the current skills itself.
It runs each track three times, freezes each project, and grades it with the track scorer:

```sh
python3 scripts/agent_eval.py run --agent "claude -p --output-format json --dangerously-skip-permissions"
```

Private held-out tracks can live outside the repository and use `--track /path/to/track`.

The evaluation references require macOS.
These requirements do not restrict the skill bundle to macOS.
The [evaluation guide](docs/evaluation.md) records the tracks, the scorer steps, and the reproduction details.

Contributors rebuild the architecture figure with `make diagram`.
The build needs LaTeX, latexmk, and Poppler.
Each skill keeps its main instructions short and stores supporting methods, templates, and helpers in its resource folders.

## Documentation

- [Product and vision](docs/product.md)
- [Architecture and diagram source](docs/architecture.md)
- [Evaluation method and dataset](docs/evaluation.md)
- [Target-project format](skills/rustify/references/project.md)
- [Standards and terminology](skills/rustify/references/standards.md)
- [Rust stack guide](skills/rustify-plan/references/rust-stack.md)

## License

Rustify uses the [GNU General Public License v3.0](LICENSE).
