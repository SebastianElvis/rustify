# Rust implementation design

The implementation uses one small synchronous CLI.
The standard library handles arguments, files, streams, and errors.
The maintained `blake3` crate supplies the cryptographic primitive.
A custom cryptographic implementation would add risk without improving the CLI recovery evaluation.
The evaluation therefore measures product reconstruction around an existing primitive.

A mode enum distinguishes unkeyed, keyed, and derived hashing.
The hashing function streams each input through a cloned hasher.
The output reader supports byte offsets and variable output lengths.
The formatter emits the observed CLI records.
The check parser validates a digest and an escaped path.
The checker accumulates failures across all records.

The implementation does not copy decompiler variable names or control flow.
The implementation does not add rayon or memory mapping.
The contract excludes performance parity.
The CLI accepts normal scoped options.
The contract excludes exact parser diagnostics for unrelated combinations.
