# ninja track

## Product

Ninja is a small build system that focuses on speed.
CMake, Meson, GN, and Chromium generate Ninja manifests.
Many large C and C++ projects build with it.

## Selection rationale

- The track adds C++ to the dataset. The other tracks use C, Rust, and Go.
- C++ adds virtual dispatch, templates, the standard library, and exceptions to the binary. These features change how the agent recovers architecture.
- The track adds a build tool with persistent state: the build log and the deps log.
- The status output, the command order, and the log formats give an exact oracle.
- The program is medium-sized (about 20,000 lines of C++). A complete user-facing reconstruction is feasible.

## Reference build

- Source: Ninja 1.13.2 from GitHub. The SHA-256 is in `reference.yaml`. The source uses the Apache-2.0 license.
- Build: `scripts/build_reference.py ninja` runs CMake in `Release` mode with interprocedural optimization and the hardened flags, then runs `strip`.
- The stripped executable retains a 7,755-byte Python helper for `browse`. Artifact recovery can expose this source. The evaluator records that exposure separately from external repository source access.

## Oracle

The `issue_2621` probe uses `-j1 -v` to fix command completion order.
The scorer runs each upstream test once.

- Byte-exact stdout, stderr, and exit status for build scenarios.
- The same executed commands in the same order.
- Mutual acceptance of `.ninja_log` and `.ninja_deps` files.
- After the source reveal: the upstream `misc/output_test.py` and `misc/jobserver_test.py` tests run unchanged against both programs.
- The upstream C++ parser, build, graph, and clean tests use internal APIs. The scorer replays their manifests, depfiles, dyndep files, and created files as black-box scenarios.
- The other C++ unit test files (for example `build_log_test.cc`, `deps_log_test.cc`, and `subprocess_test.cc`) have no black-box form. Each upstream report records its test count and the tests with cases.

## Reports

- `replay-core`, `replay-extended`, `replay-complete`: the evaluator's multi-step scenarios in three milestones.
- `replay-persistence`: the same scenarios with the programs alternating per step, in both orders. Each program must continue the `.ninja_log` and `.ninja_deps` files of the other.
- `replay-browse`: nine fixed headless HTTP workflows from `cases.yaml`. The evaluator tests graph navigation, escaped names, live manifests, request boundaries, startup errors, help, and termination.
- `generate-scenarios`: seeded random manifests, flags, tools, state changes, and damaged manifests (`generate.py`).
- `upstream-<file>`: one report per upstream test file.
- `repeatability`: the reference against itself on every scenario.
- A wrapper that deletes `.ninja_log` after each run is the negative control. It must fail.
- The repeatability report keeps browse controls and legacy counts separate. A control without an HTTP service must fail.

## Variable fields

`runner.py` applies only these equivalence rules. Every other difference is a witness.
The runner preserves raw streams and file bytes before normalization.
The `raw_files` records keep exact timestamps, ownership, and filesystem identity.
The reports use YAML binary values for stream bytes, file bytes, and filenames.
The representation preserves invalid UTF-8 bytes.

| Field | Rule | Evidence |
| --- | --- | --- |
| Start and end times in `.ninja_log` | Replaced by `*`. | `build_log.cc` writes milliseconds since the build start. |
| Nanosecond timestamps in `.ninja_log`, `.ninja_deps`, `-t deps`, and `-d explain` | A value inside the wall-clock window of the scenario becomes `<wall>`. Fixture timestamps stay exact. | `build.cc` records the mtime of `.ninja_lock` at the edge start and the output mtime after the command. `graph.cc` and `ninja.cc` print these values. |
| `-t graph` node identifiers | Renumbered in the order of first use. | `graphviz.cc` prints node and edge addresses with `%p`. ASLR changes them on each run. |
| The scenario directory path | Replaced by `$ROOT`. | `-t compdb` and command output print the working directory. Each run uses a new temporary directory. |

- The default `-j` value in the usage text is the CPU count plus 2. The scorer does not change it, because both programs run on the same host.
- The `NINJA_STATUS` placeholders `%e`, `%w`, `%E`, `%W`, `%o`, and `%c` print elapsed time and rates. The cases do not use them, and `-d stats` prints timings. These features stay in scope without an exact case.
- The interrupt cases send the signal 0.1 seconds after the command creates a marker file.
- The runner keeps stdin open and preserves merged streams and PTYs.
- The supervisor applies one total deadline to each step. A missing signal marker makes the capture incomplete.
- The `browse` tool resolves a `python` executable through `PATH` at runtime. The scorer's controlled `PATH` reaches `ninja: python is required for the browse tool`. A task-owned interpreter link enables headless HTTP probes with `--no-browser`.

`browse.py` preserves raw captures for every HTTP workflow.
The evaluator replaces only the selected loopback port, the reported server PID, and a valid current HTTP Date header.
The evaluator keeps other bytes exact.
The evaluator requires complete target and worker termination records.
The evaluator checks each observed PID with its recorded start time.
The evaluator sends no terminal cleanup signal to a reused PID.
The evaluator pins `compare.py` to its recorded hash.
A different helper requires qualification before these measurements apply.
Each target uses a 15-second deadline, 512 MiB, 32 processes, 8 MiB of output, and a zero core limit.
Each worker uses a 22-second deadline and 2 GiB.
The supervisor samples resource use. It does not provide hard containment.

## Scope

- The scope is the full product. Rustify always targets a complete one-to-one reconstruction.
- The scorer measures the features that its cases cover. A feature without a case stays in scope.
- A failed or missing feature is a skill defect. The fix goes into the skills, not into a narrower scope.
- The full product covers the complete manifest language, all flags, all `-t` tools including `browse`, and the build and deps logs.
- `run.py` scores a project in `work/projects/ninja` and writes reports to `work/evaluation/ninja/`.
