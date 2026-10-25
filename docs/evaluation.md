# Evaluation

Rustify evaluates a reconstruction against an identified original binary.
The report separates measured behavior from unexplored behavior.
The default reconstruction requires one-to-one product, UX, component, data, and behavior mappings.
Each track asks the agent for the full product.
A track scorer measures only its own cases.

## Complete flow

1. The evaluator selects an open-source target with test vectors and pins its binary.
2. The evaluator records the binary origin, version, platform, license, and SHA-256.
3. The reconstruction receives only the binary, resources, skill, and execution environment.
4. Discovery captures product, experience, architecture, and reproducible scenarios.
5. Planning defines acceptance checks before implementation.
6. The reconstruction implements idiomatic Rust with unit and E2E tests.
7. The evaluator freezes the Rust source hash and discovery artifacts.
8. A separate evaluation pass adds challenge cases.
9. The evaluator reveals the original source and upstream vectors.
10. The evaluator compares product coverage, architecture recovery, and behavior separately.
11. A failure preserves a reproducer. A repair repeats the affected checks.
12. The final report states source access, repairs, measured coverage, and remaining gaps.

The target project separates `recovered/`, `implementation/`, and `verification/`.
The target project keeps the Rust design and decision records in `implementation/docs/`.
The recovered test specifications record observable expectations and their origin.
The verification folder records execution results.

The source audit must not quietly become a source translation pass.
The evaluator records source-assisted changes separately if they become necessary.
The evaluator does not claim perfect isolation when one agent performs both passes.

## CLI comparison

Each scenario contains these fields:

```yaml
- id: encode-stdin
  args: [-w, '0']
  stdin_b64: aGVsbG8=
  files: {}
```

The `stdin_b64` and file values encode raw bytes.
Optional `env` entries configure uncontrolled variables.
The helper reserves locale, timezone, home, and path variables.

```sh
python3 skills/rustify-validate/scripts/compare.py --reference /path/to/original --candidate /path/to/implementation --cases PROJECT/recovered/scenarios.yaml --report PROJECT/verification/comparison.yaml --name base64
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
| Compression | bzip2 1.0.8 | The complete `bzip2` command and byte-exact `.bz2` output. |
| Interpreter | Lua 5.5.1 | The command line, the language core, and the deterministic standard libraries. |
| Database | SQLite 3.54.1 shell | Shell basics, core SQL, and rollback-journal database files. |
| Build tool (C++) | Ninja 1.13.2 | The manifest language, dirty checks, logs, flags, and tools. |
| Game | doomgeneric with Freedoom 0.13.0 | Startup, WAD loading, demo simulation, and the software renderer. |

Each track folder has a `README.md` with the product, the selection rationale, the reference build, the oracle, and the scope.
`evaluations/README.md` explains the dataset design and its relation to published benchmarks.

## Reference builds

The first four tracks pin upstream release binaries.
The upstream projects control their compiler flags.
The last five tracks pin a hardened local build from pinned source.
`scripts/build_reference.py <track>` reads `evaluations/<track>/reference.yaml` and builds the binary in `work/references/<track>/`.

- The C and C++ flags are `-O3 -flto -fvisibility=hidden -DNDEBUG`.
- The link flags are `-flto -Wl,-dead_strip`.
- The script runs `strip` on the result.
- The script deletes the source tree after the build.

Optimization inlines code and changes its structure.
Stripping and hidden visibility remove the symbol names.
`-DNDEBUG` removes assertion strings that contain source paths.
The script records a metadata audit in `build.yaml`: the defined symbols, the source-file strings, and the build-path leaks.
Each hardened reference keeps one defined symbol.

The build is deterministic for one compiler version.
`reference.yaml` pins the binary SHA-256 and the compiler.
The scorer rebuilds a missing reference and rejects a different hash.
Go and Rust binaries keep more metadata after `strip`.
Go keeps function and type names in its runtime tables.
Rust keeps panic locations unless the build remaps or removes them.

The repository stores the dataset, not agent outputs.
Each track folder has a `run.py` scorer and its pinned reference, cases, and upstream vectors.
`evaluations/harness.py` provides the shared download, freeze, Rust checks, and report steps.

1. The scorer downloads and verifies the reference in `work/downloads/<track>`.
2. The agent reconstructs that binary into `work/projects/<track>`.
3. The agent receives only the binary and the skill.
4. The scorer records the hash of each project file before it reveals any case.
5. The scorer runs Cargo format, Clippy, test, and release build checks.
6. The scorer compares the Rust executable with the reference on its own cases and upstream vectors.
7. The scorer writes its reports in `work/evaluation/<track>/`.

Git ignores `work/`.
A run without a project still downloads the reference and then fails.
The scorer reports the project checkpoint state but does not require it.

The default evaluation scores the CLI, cryptography, and client tracks.
The desktop option also scores the zenity track.
The scorer does not open dialogs.
The operator replays the five cases with host-native CUA on both executables.
The operator saves the captures and a visual review in `verification/gui-captures/` of the project.
The scorer accepts only captures of the reference and of the executable that it builds.

```sh
make evaluate
python3 scripts/evaluate.py --desktop
python3 evaluations/open/xh/run.py --project /path/to/project
```

The first run needs internet access for pinned binaries and Cargo dependencies.
Later runs use local inputs and loopback HTTP.
The dataset requires macOS and the reference binaries' CPU support.
The skill bundle remains host-neutral.

## Agent evaluation

The scorers above grade one project. The agent evaluation also produces the projects.
`scripts/agent_eval.py` runs the current skill bundle with an agent command on each track.

1. The harness downloads the pinned reference with the track's `run.py` pin.
2. For each trial, it creates a workspace with the installed skills and a copy of the binary.
3. It sends a blind prompt on standard input. The prompt forbids the original source, tests, and documentation.
4. It records the time, the return code, and the token use and cost when the agent reports them.
5. It freezes the hash of each project file after the agent exits.
6. The `grade` step rejects a project that changed after the freeze.
7. It runs the track scorer, the parity gate, and the quality measures on each trial.

```sh
python3 scripts/agent_eval.py run --agent "claude -p --output-format json --dangerously-skip-permissions" --trials 3
python3 scripts/agent_eval.py grade work/agent-eval/<stamp>
```

The harness never repairs a project. Every score is a blind score.
The default tracks are base64, b3sum, and xh. The desktop track needs an operator.

### Held-out tracks

The public tracks are well-known programs. A model can know their source from training.
Their scores can therefore overstate blind reconstruction.
The evaluator keeps private held-out tracks outside the repository.

- A private track is a folder with `run.py`, `grading.yaml`, and its cases.
- Its `run.py` adds the repository `evaluations/` folder to `sys.path` and calls `harness.run`.
- The evaluator writes small programs that are not public, builds them without symbols at two optimization levels, and pins their hashes.
- The evaluator includes at least one program with persistent state and one network service.
- The evaluator never commits the program, its source, or its cases.

```sh
python3 scripts/agent_eval.py run --agent "AGENT COMMAND" --track /private/tracks/ledger-tool
```

### Grading data

Each track has `grading.yaml` with feature patterns and component patterns.
The patterns come from the original source and its documentation.
The agent never sees `grading.yaml`.

## Evaluation checks

- The original passes a repeatability comparison against itself.
- Unit tests verify encoding logic, partial results, and boundary conditions.
- E2E cases verify command parsing, input files, and errors.
- Challenge cases exercise malformed and generated inputs.
- Upstream vectors run against both executables after the source reveal.
- A deliberately wrong implementation fails the comparison.
- Resume tests detect changes to inputs and Rust source.

## Scores

| Dimension | Measure | Oracle |
| --- | --- | --- |
| Blind behavior | Passed cases divided by all scored cases, without repairs. | The track cases and upstream vectors. |
| Reliability | pass@k and pass^k over the trials. A trial passes when its scorer passes. | The track scorer. |
| Product recall | Feature patterns found in the requirements, divided by all feature patterns. | `grading.yaml` |
| Architecture recall | Component patterns found in the recovered components, divided by all component patterns. | `grading.yaml` |
| Structural fidelity | Original components with their own Rust module, divided by all original components. | The reflexion check. |
| Edge convergence | Converged original edges, divided by converged and absent edges. | The reflexion check. |
| Parity gate | The assessment, errors, and gap count. | `parity.py` |
| Test adequacy | The mutation score from `cargo mutants`. | `verification/checks.yaml` |
| Rust quality | Clippy pedantic warnings and `unsafe` uses. | Clippy and the source. |
| Cost | Wall time, tokens, and cost. | The agent output. |

Pattern recall is a coarse measure. A match does not prove a correct requirement.
The evaluator audits a sample of requirements against the source to estimate precision.

## Parity gate

The parity gate reads the ledger `recovered/model.yaml`.
It computes each requirement result from evidence and captures and runs the reflexion check.
It checks that the documents name every requirement, component, and open gap.
A passing machine gate does not prove that the declared inventory covers every original feature.
The agent must justify that inventory with evidence.

```sh
python3 skills/rustify-validate/scripts/parity.py --project PROJECT --report PROJECT/verification/parity.yaml
```
