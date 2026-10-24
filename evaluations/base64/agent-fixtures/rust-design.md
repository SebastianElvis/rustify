# Rust design

The replacement uses the Rust standard library.
The project needs no external dependency.
The project rejects a CLI library because exact GNU errors need a small custom parser.
The parser uses byte arguments to preserve Unix filenames.
The parser supports GNU option permutation and POSIXLY_CORRECT.
The codec uses small state values and fixed buffers.
The encoder keeps its three-byte quantum across reads.
The decoder keeps its four-character quantum across reads.
The decoder emits partial bytes before it reports an error.
The output wrapper keeps a column counter.
The I/O layer reports errors at the CLI boundary.
The project uses safe Rust.
The project rejects a whole-file buffer because pipelines need bounded memory.
The recovered C procedure structure does not define Rust modules.
The initial implementation uses one small binary module.
The help and version resources preserve exact binary output.
The tests use tables and short readers to check state across boundaries.
The design preserves observed numeric overflow behavior.
The design treats source intent as unknown.

The replacement duplicates stdout into an owned File descriptor.
This choice prevents Rust stdout from suppressing EBADF write failures.
The replacement reports an input error before a final output error.
The replacement removes duplicate write diagnostics.
The project excludes descriptor exhaustion and closed startup descriptors.
The host linker settings changed during the investigation.
The check script selects the Apple linker explicitly.
The project preserves the failed linker output in `evidence/toolchain-failure-test.log`.

The migrated target stores recovered specifications in `recovered/`.
The Cargo package lives in `implementation/`.
The verification reports and logs live in `verification/`.
The temporary agent workspace owns this design and `plan.json`.
The layout migration changes no frozen implementation bytes.
