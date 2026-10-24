# Base64 source audit

The source audit confirms the recovered CLI capabilities and major workflow edges.
The frozen Rust replacement passes the complete upstream base64 vector set.
The audit finds no upstream case that requires a Rust repair.

## Source isolation and identity

The reconstruction did not see original source before its SHA-256 freeze.
The parent revealed GNU coreutils 9.12 source after that freeze.
The source archive SHA-256 is `a480198559733e9b3da999e90543ac6f888a2caa544d8d664c5a1f17e528e210`.
The pinned arm64 reference SHA-256 is `41dd92cf260491c5c8fc0084c42e58b1baaca9ebcc88aa38f60a17a2ef603570`.
The replay verifies all five frozen replacement files before its build gates.
The initial freeze remains unchanged.
The source audit introduces no source-assisted Rust change.
The same agent performed the blind reconstruction and this later audit.
The evaluation therefore claims source isolation before the freeze, not separate audit personnel.

## Product capabilities

The table compares `../recovered/product.md` with the revealed source.

| Recovered capability | Original source evidence | Audit result |
| --- | --- | --- |
| Encoding, decoding, and one input | `src/basenc.c:main`, lines 1629 and 1804–1832 | The source selects stdin, dash, or one binary input file. It selects one codec workflow. |
| Decode, garbage, wrap, help, and version options | `src/basenc.c:long_options`, line 74; `usage`, line 96; `main`, line 1654 | The base64 build exposes the recovered options. Other encodings belong to different build modes. |
| Default wrapping and numeric behavior | `src/basenc.c:main`, lines 1640 and 1664–1675; `wrap_write`, line 1442 | The source uses 76 columns. Zero and positive signed overflow disable wrapping. |
| LF and optional garbage handling | `lib/base64.c:get_4`, line 318; `src/basenc.c:do_decode`, line 1561 | The decoder ignores LF. The optional filter removes other non-alphabet bytes while preserving padding. |
| Canonical padding and partial output | `lib/base64.c:decode_4`, line 372; `src/basenc.c:decode_ctx_finalize`, line 413 | The source rejects nonzero pad bits. The finalizer can add missing padding. The output retains bytes before an error. |
| Diagnostics and output completion | `src/basenc.c:main`, `finish_and_exit`, `do_decode`; `atexit(close_stdout)`, line 1652 | The source checks options, files, reads, writes, and input completion. Exact exceptional lifecycle coverage remains limited. |

The source confirms the recovered product scope.
The audit does not infer the creator's future plans from source structure.

## Original architecture

The table compares `../recovered/architecture.md` with source components.

| Recovered edge | Original component | Audit result |
| --- | --- | --- |
| Main → option parser → input selection | `src/basenc.c:main`, `getopt_long`, `fopen`, `fadvise` | The recovered control flow matches. |
| Main → block encoder → wrapper | `do_encode` → `base64_encode` → `wrap_write` | The source uses 30720 input bytes and 40960 encoded bytes per full block. |
| Main → filtered block decoder → context decoder | `do_decode` → `base64_decode_ctx` | The source uses 4096 encoded input bytes and 3072 output bytes. |
| Context decoder → partial quantum handling | `lib/base64.c:base64_decode_ctx`, `get_4`, `decode_4` | The recovered model identifies state across blocks. It does not recover these internal fast paths. |
| Decoder completion → optional padding | `src/basenc.c:decode_ctx_finalize` | The revealed source confirms the behavior that probes recovered. |
| Workflow → input close → output close | `finish_and_exit` and the registered `close_stdout` handler | The recovered lifecycle edge matches. Exact close failures remain outside measured coverage. |

The source uses compile-time `BASE_TYPE == 64` aliases for shared basenc code.
The blind model does not identify the complete shared multi-encoding framework.
That framework does not add options to this base64 binary.
The source also uses gnulib helpers for parsing, quoting, localization, allocation, and diagnostics.
The blind model recovers their visible boundaries, not their complete internal implementations.

## Behavior and upstream conversion

The audit executes the unchanged `tests/basenc/base64.pl` generator.
A small exporter captures its `run_tests` argument only for the base64 branch.
The generator produces all 201 base64 vectors.
The generator file SHA-256 is `354bdef5572a188f1c92c89759cb243170c9187b317ff5506625af9a18a629e9`.
The audit independently verifies each exported argument, input, output, and status.
The generated text uses ASCII, so the JSON-to-byte conversion preserves its bytes.
The generator's automatic decode and newline variants remain intact.

`tests/Coreutils.pm`, lines 75–95 and 533–561, defines the expected-output substitutions and defaults.
The exporter preserves empty stdout and stderr defaults and zero exit defaults.
The exporter converts the three `base..:` placeholder diagnostics to concrete `base64:` diagnostics.
The exporter converts the invalid-input substitution to the concrete C locale diagnostic.
These concrete checks are stricter than the upstream prefix-removal rule.
The replay asserts those expected values separately for the reference and replacement.
Program agreement alone does not satisfy this gate.

The replay passes 279 separate challenge cases and 201 upstream vectors.
The reference passes all 480 cases against itself.
Both programs pass all 402 expected-output assertions for the upstream vectors.
The archived blind run records 8145 earlier E2E cases.
The default replay does not rerun that larger archive.
The replay does not run the complete coreutils or gnulib test suites.
The large-input and bounded-memory shell tests target broader basenc modes.
This replay does not claim those shell-test results or a formal memory bound.

## Rust choices

The Rust implementation intentionally uses a different internal architecture.
The replacement uses a custom byte-argument parser and small codec state values.
The replacement uses fixed input buffers and a buffered output descriptor.
The replacement uses safe standard-library code and no external dependency.
The owned stdout descriptor preserves tested EBADF write errors that Rust stdout suppresses.
The Rust design avoids the C macro framework and gnulib helper graph.
The Rust design does not copy decompiler registers or optimized C control flow.
The formatting, clippy, ten unit tests, and release-build gates pass.

All coverage claims remain finite.
The C locale and macOS arm64 contract still excludes other locales, platforms, exact signals, resource exhaustion, startup descriptor repair, and interruption timing.
Fresh release binaries can differ across host toolchains.
The replay verifies frozen source identity and records each new executable hash.

## Layout migration

The target project now contains only `recovered/`, `implementation/`, and `verification/`.
The original freeze remains byte-for-byte intact at `../recovered/evidence/freeze-manifest.json`.
The blind archive remains at `../recovered/evidence/blind-run.tar.gz`.
The replay maps historical `replacement/` entries to current `implementation/` paths when it verifies source hashes.
The migration changes no frozen Rust or resource bytes.
The migration introduces no source-assisted implementation change.
The agent workspace keeps temporary design and plan files outside the target project.
The recovered declarative specifications distinguish observed evidence from proposed challenge cases.
The upstream specifications use observed origins with an upstream source reference.
