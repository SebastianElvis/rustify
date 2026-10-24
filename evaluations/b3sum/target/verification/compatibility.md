# BLAKE3 compatibility

The Rust implementation uses the approved `blake3` crate.
The evaluation compares the released b3sum 1.8.7 macOS x86_64 binary under Rosetta.
The target identity is in `../recovered/evidence/target-provenance.json`.

The runtime suite has 226 cases.
The repeatability suite checks all 226 cases against the original.
The official vector suite has 315 cases from 35 input lengths and three modes.
Both executables must pass 630 independent expected-output assertions.
The Rust package has four unit tests and four process tests.
The wrong-output control must fail.
The runner also checks the declarative expectations in `../recovered/tests.json`.

The binary-only implementation passes 220 runtime cases after two runtime repairs.
The source audit adds six boundary cases and one source-assisted patch.
The archive and original freeze manifests in `../recovered/evidence/` preserve that history.
The layout migration does not change Rust code or Cargo files.
The evaluator uses one agent for reconstruction and the later source audit.
The evaluation does not claim complete assessor isolation.

The contract excludes exact diagnostics for unsupported option combinations.
The contract excludes threading, memory-mapping performance, and non-UTF-8 paths.
The contract excludes a checkfile that references stdin while stdin supplies that checkfile.
The original blocks on that case during discovery.
These finite tests do not prove arbitrary-binary equivalence.

The wrapper `../../run.py` replays the evaluation from any directory.
The current result is `summary.json`.
Current logs and full reports stay in `logs/` and `raw/`.
The external agent workspace stores the Rust design and implementation plan.
