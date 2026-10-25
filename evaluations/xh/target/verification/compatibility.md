# xh evaluation results

The evaluation reconstructs a finite local HTTP contract from xh 0.26.3.
The original binary is a pinned macOS arm64 release.
The reconstruction receives no original source or tests before its freeze.

## Results

| Check | Result |
| --- | --- |
| Binary-only process comparisons | The candidate passes 26 cases. |
| Binary-only protocol comparisons | The candidate passes 26 cases. |
| Original repeatability | The original passes 26 cases against itself. |
| Source-audit expectations | Both executables pass 13 independent vectors after the recorded repair. |
| Rust unit tests | Six tests pass. |
| Process E2E tests | One test runs the 26 process and protocol cases. |
| Rust quality | Formatting and Clippy pass. |
| Resume state | All five checkpoints are current. |

`summary.json` records the latest executed result.
`raw/` contains complete reports. `logs/` contains command logs.
`comparison.json` contains a compact index of the process comparison.

## Corrections

The binary-only challenge exposes two request-item separator defects.
The repair selects the first separator and preserves its regression cases.
The source audit later exposes three additional causes across eight new vectors.
`source-audit.md` and `source-assisted.patch` disclose those source-assisted repairs.
`../recovered/evidence/binary-only-evidence.zip` preserves the pre-reveal source, models, and failing captures.

## Product and architecture

The evidence supports the scoped GET, HEAD, POST, JSON, header, redirect, and status workflows.
The source confirms the recovered functional responsibilities.
The source reveals a blocking original transport and a wider middleware design.
The implementation now preserves the original blocking reqwest execution model.
The repair removes the direct Tokio dependency and async entry point.
Reqwest still has a transitive Tokio dependency.
The report does not claim identical internal architecture.

## Limits

The fixture server binds only to `127.0.0.1`.
The candidate also rejects external HTTP destinations and redirect targets.
The protocol comparison checks method, path, body bytes, and selected headers.
The contract permits header order and transport defaults to differ.
The upstream vectors also check repeated header values and absent content headers.

The contract excludes TLS, proxies, authentication, sessions, uploads, downloads,
compression, pretty output, stdin bodies, nested request-item syntax, and unlisted options.
The report does not claim complete xh equivalence or full upstream-suite coverage.

## Reproduction

The evaluator runs `python3 /path/to/rustify/evaluations/xh/run.py`.
The runner accepts any working directory.
The runner resolves all repository paths from its own location.
The runner fetches the pinned reference only when the executable is absent.
The runner verifies archive and binary hashes before execution.
The runner runs Rust quality checks and all local evaluations.
The runner writes a failed summary and returns a nonzero status on failure.

The host's configured Homebrew linker rejects the installed SDK.
The runner selects the system linker in its Darwin command environment.
The runner preserves an explicit `RUSTFLAGS` setting.
The runner changes no global configuration.

## Strict-parity status

This example remains a partial body-only loopback HTTP evaluation.
Strict full-product parity remains unestablished.
The blocking execution repair follows source reveal and the earlier CLI repair.
The runtime Rust change adds 7 lines and removes 7 lines.
The implementation source remains at 278 lines.
The parser and test source bytes remain unchanged.
`blocking-faithfulness.json` and `blocking-faithfulness.patch` record the new repair.
`../recovered/evidence/source-assisted-before-blocking.zip` preserves the previous candidate and patch.
The initial binary-only freeze and archive remain unchanged.

The original middleware, complete CLI, printer, stateful features, and wider transport configuration remain open gaps.
The original redirect-limit error path is not equivalent to the current reqwest policy stop.
The implementation uses a different reqwest version and a smaller feature set.
The finite contract retains its stated header-order and selected-default allowances.
Those allowances do not establish strict full-product parity.
`../recovered/component-mapping.md` and `../recovered/roadmap.md` track the remaining gaps.
