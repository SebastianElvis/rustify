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

- Source: bzip2 1.0.8 from `sourceware.org`. The SHA-256 is in `reference.yaml`. The source uses the bzip2-1.0.6 (BSD-style) license.
- Build: `scripts/build_reference.py bzip2` compiles the eight C files with the hardened profile and runs `strip`.
- The build log and metadata audit go to `work/references/bzip2/build.yaml`.

## Oracle

- Byte-exact comparison of compressed output against the reference for generated inputs and all levels.
- Cross-decompression in both directions.
- After the source reveal: the upstream `sample1` to `sample3` reference files and the upstream `make test` vectors.

## Scope

- The scope is the full product. Rustify always targets a complete one-to-one reconstruction.
- The scorer measures the features that its cases cover. A feature without a case stays in scope.
- A failed or missing feature is a skill defect. The fix goes into the skills, not into a narrower scope.
- The full product is everything the `bzip2` binary does, including its behavior when the program name is `bunzip2` or `bzcat`.
- `run.py` scores a project in `work/projects/bzip2` and writes reports to `work/evaluation/bzip2/`.

## Reports

- `replay-core`, `replay-extended`, and `replay-complete` hold the hidden milestone cases.
- `generate-options` holds 610 seeded probes: every pair of short flags, then random option sets, input formats, and file layouts.
- `metamorphic-roundtrip` decompresses the output of each program with the other program.
- `upstream-tests` holds the six `make test` commands. The scorer also checks their expected bytes.
- `upstream-samples` holds other cases from the upstream sample files.
- `repeatability` runs every case on the reference twice.
- Each case id is `<feature-id>/<case-name>`. The feature ids come from `grading.yaml`.

## Variable fields

- The view has no variable field. The same input, flags, and file layout give the same bytes on stdout, stderr, and files.
- The exit status is fixed. The repeatability report confirms all three channels.
- The `perror` line after an unexpected end of input shows the last `errno`. With a pipe on stdin, the reference prints `Inappropriate ioctl for device` on every run. The scorer compares this line exactly.
- The reference copies the mode and the modification time of the input to the output file. `compare.py` does not capture modes or times, so the scorer does not measure them.
