# Base64 compatibility

The frozen Rust replacement passes the compact independent replay.
The source audit requires no Rust repair.

| Check | Result |
| --- | --- |
| Frozen replacement files | All 5 hashes match. |
| Formatting, clippy, and release build | All gates pass. |
| Unit tests | All 10 tests pass. |
| Independent challenge cases | All 279 cases pass. |
| Original upstream base64 vectors | All 201 vectors pass. |
| Upstream expected-output assertions | All 402 checks pass across both programs. |
| Reference self-repeatability | All 480 cases pass. |
| Archived blind E2E evidence | All 8145 earlier cases pass. |

The default replay runs 480 comparison cases.
The replay compares stdout, stderr, exit status, and fixture files exactly.
The upstream gate also checks explicit expected outputs for each program.
The replay does not rely on program agreement alone.

The implementation supports encoding, decoding, stdin, dash, one file, wrapping, garbage filtering, GNU option parsing, help, version, and tested diagnostics.
The implementation preserves partial decode output, padding checks, canonical missing padding, and concatenated groups.
The revealed source confirms the recovered capabilities and major architecture edges.
The Rust implementation intentionally uses a different internal architecture.
The file `source-audit.md` records source paths, symbols, conversion rules, and architecture limits.

The initial freeze precedes original-source access and external challenge feedback.
The replay checks source hashes before every build.
The replay records fresh executable hashes without claiming identical release binaries across toolchains.
The replay preserves the initial freeze and introduces no source-assisted Rust change.

The contract covers macOS arm64 in the C locale.
The measured coverage does not prove arbitrary-input equivalence.
The tests do not establish exact signals, resource exhaustion, descriptor scheduling, startup descriptor repair, or interrupted-I/O timing.
The replay does not run the entire coreutils or gnulib suite.
The default replay keeps the 8145-case blind evidence in `../recovered/evidence/blind-run.tar.gz`.

The user can run `python3 evaluations/base64/run.py` from the repository root.
The user can also run that file by absolute path from any directory.
The runner writes raw reports and command logs under `evaluations/base64/target/verification/raw/` and `logs/`.
The runner writes its current result to `evaluations/base64/target/verification/summary.json`.
The runner selects the Apple linker locally only after a host linker failure.

The layout migration preserves the original freeze and every frozen implementation byte.
The current target has `recovered/`, `implementation/`, and `verification/` folders.
The replay maps historical `replacement/` paths to `implementation/` without rewriting the historical manifest.
The recovered scenario list retains 8196 CLI scenarios from the blind and later evaluation sets.
The declarative specifications retain 8625 E2E cases, including archived raw-argument and descriptor scenarios.
The fast replay selects the 279 independent cases and all 201 upstream vectors.
The replay completes all five current project checkpoints.
Temporary design and plan files remain in an external agent workspace.
