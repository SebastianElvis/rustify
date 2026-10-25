# Rustify

**Closed source should not block reconstruction.**

Rustify gives AI agents a workflow to reconstruct software from a binary in idiomatic Rust.
It recovers product specifications, UX, architecture, evidence, and tests alongside the implementation.
Rustify depends on [REA](https://github.com/morluto/rea) for reverse engineering.
The goal is software that you can inspect, build, and maintain without the original source.

## Installation

The setup below uses Node.js 24.x (24.22.1 or later), npm, Python 3, and Rust with Cargo.

### 1. Set up REA

REA supplies the tools for product, UX, and architecture discovery.

```sh
npx rea-agents setup
```

You select the agents that will use REA.
You review the proposed configuration and approve the changes.
Setup registers the MCP server and installs REA's matching workflow instructions.
You restart the agents named in the completion message.

Native binary analysis needs Hopper, Ghidra, or IDA.
Setup can connect an existing Hopper or Ghidra installation.
It can also install Hopper when you select that option.
Other target types can use REA's built-in inspection tools.
The [REA setup reference](https://github.com/morluto/rea/blob/main/docs/installation.md) provides additional provider settings and troubleshooting steps.

### 2. Install Rustify

You run this command from your project folder:

```sh
npx skills add SebastianElvis/rustify --skill '*'
```

The [Skills CLI](https://github.com/vercel-labs/skills) installs all seven Rustify skills and prompts you to select your agents.
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
Your agent must expose the REA tools before reconstruction starts.

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

- **We strive for one-to-one mapping.** Rustify maps the original product, UX, behavior, data, and architecture to the Rust implementation. Known differences remain open until a repair resolves them.
- **Evidence and user experience guide reconstruction.** Observed workflows, interface states, binary evidence, and tests support each mapping. Unit tests, E2E comparisons, independent expectations, and available upstream vectors challenge the result.
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
The repository stores the pinned references, cases, and scorers, not agent outputs.
You reconstruct each reference into `work/projects/<track>` with your agent.
`make evaluate` scores the first three tracks.
The `--desktop` option also scores saved GUI captures:

```sh
python3 scripts/evaluate.py --desktop
```

The evaluation references require macOS.
These requirements do not restrict the skill bundle to macOS.
The [evaluation guide](docs/evaluation.md) records the scopes, the scorer steps, and the reproduction details.

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
