# bzip2 track

## Product

bzip2 is a block-sorting file compressor.
Julian Seward released it in 1996.
Most Unix systems and many archive tools ship it.
The `.bz2` format uses the Burrows-Wheeler transform, move-to-front coding, run-length coding, and Huffman coding.

## Selection rationale

- The track adds a compression codec to the dataset.
- The codec has a stable binary file format and a byte-exact oracle: the same input and flags give the same output bytes.
- The codec contains dense bit-level loops. Optimization inlines and unrolls these loops. The agent must recover the algorithms from optimized machine code.
- The CLI has many flags, file-naming rules, and exit codes. The track tests CLI fidelity as well as the codec.
- The program is small (about 8,000 lines of C). A complete reconstruction is feasible.

## Reference build

- Source: bzip2 1.0.8 from `sourceware.org`. The SHA-256 is in `reference.json`.
- Build: `scripts/build_reference.py bzip2` compiles the eight C files with the hardened profile and runs `strip`.
- The build log and metadata audit go to `work/references/bzip2/build.json`.

## Oracle

- Byte-exact comparison of compressed output against the reference for generated inputs and all levels.
- Cross-decompression in both directions.
- After the source reveal: the upstream `sample1` to `sample3` reference files and the upstream `make test` vectors.

## Scope and limits

- The scope covers the complete `bzip2` command.
- The scope excludes `bzip2recover`, `bzcat`, `bzgrep`, and the `libbz2` C API.
- `evaluations/bzip2/run.py` scores a project in `work/projects/bzip2` and writes reports to `work/evaluation/bzip2/`.
