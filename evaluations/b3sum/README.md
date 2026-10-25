# b3sum track

## Product

`b3sum` is the command-line tool for the BLAKE3 cryptographic hash function.
The BLAKE3 team develops it in Rust.

## Selection rationale

- The track adds cryptography and a Rust-compiled binary to the dataset.
- Hash outputs are exact. One wrong bit changes the whole digest.
- BLAKE3 has official test vectors for hashing, keyed hashing, key derivation, and extended output.
- The agent must recover SIMD-dispatched and heavily inlined compression code.

## Reference build

- Binary: `b3sum_macos_x64_bin` from the BLAKE3 1.8.7 GitHub release. It runs under Rosetta on arm64.
- The upstream release controls the flags.
- Metadata audit: the binary is not stripped. 2,891 defined symbols remain. The strings contain 139 Rust source paths, for example `src/main.rs`.
- The leaked symbols make this track easier than a hardened build. A future revision can rebuild it with the hardened Rust profile.

## Oracle

- Byte-exact runtime comparison for 226 cases.
- After the source reveal: 315 official vector cases with 630 expected-output checks.

## Scope

- The scope is the full product. Rustify always targets a complete one-to-one reconstruction.
- The scorer measures the features that its cases cover. A feature without a case stays in scope.
- A failed or missing feature is a skill defect. The fix goes into the skills, not into a narrower scope.
- The full product covers every option of `b3sum`, including hashing, keyed hashing, key derivation, extended output, checksum checking, and the threading options.
- The first evaluation run needed source-assisted repairs. The Git history before commit `ce882f1` keeps that run.
- `run.py` scores a project in `work/projects/b3sum` and writes reports to `work/evaluation/b3sum/`.
