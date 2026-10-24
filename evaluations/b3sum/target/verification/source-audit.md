# BLAKE3 source audit

The evaluator froze the model and Rust source before source access.
The first freeze is `freeze.json`.
The repaired runtime freeze is `runtime-freeze.json`.
The source reveal time is in `source-provenance.json`.
The approved dependency supplied BLAKE3 before source reveal.
This evaluation reconstructs the CLI around that primitive.
It does not independently reconstruct BLAKE3 compression.

## Architecture findings

| Recovered claim | Source confirmation | Result |
| --- | --- | --- |
| The entry point parses options and dispatches hashing or checks. | `Args::parse` and `main` | The claim is correct. |
| The path function creates a digest reader. | `hash_path` clones the base hasher and returns `finalize_xof`. | The claim is correct. |
| Output supports raw, hex, and escaped names. | `hash_one_input`, `write_hex_output`, and `filepath_to_string` | The claim is correct. |
| The checkfile function processes multiple records. | `check_one_checkfile` calls `check_one_line`. | The inferred claim is correct. |
| The binary uses parallel file hashing. | `hash_path` uses `update_mmap_rayon`; `main` creates a Rayon pool. | The inferred claim is correct. |
| Exact crate versions remain unknown from symbols. | The dependency metadata section is absent. | The limitation remains correct. |

## Source-assisted repairs

The original binary-only implementation passes 220 runtime cases after two runtime repairs.
The source audit adds six boundary cases.
The implementation fails all six before the audit repair.
The saved report is `audit-first.json` in `blind-run.tar.gz`.
The repair rejects NUL and implementation-character paths.
The repair preserves escaped check records and tagged split precedence.
The repair propagates invalid UTF-8 errors.
The repair rejects stdin file input in keyed mode.
The repair uses `blake3::Hash` equality for constant-time comparison.
The patch adds 36 source lines and removes 36 source lines.
The report labels this patch as source-assisted.

## Independent expected outputs

The official JSON provides 35 input lengths and three modes.
Each input repeats bytes 0 through 250.
The runner checks all 35 lengths in hash, keyed, and derive-key modes.
Each mode checks the 32-byte prefix, the complete 131-byte XOF, and the 68-byte XOF slice at offset 63.
The runner checks official expected bytes against each executable separately.
Matching executable outputs alone cannot satisfy this gate.

The source archive is the official BLAKE3 1.8.7 tag archive.
Its SHA-256 is `c6782a28842b1c0478524ac06a4f2ede784038ee298d6e2162c0b089c4306a3c`.
The vector file SHA-256 is `dcb91ea8accc77e6d6e632af7cdc1a99a9f3ae78cf648da595c7d064db32f624`.
