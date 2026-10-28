# base64 track

## Product

GNU `base64` encodes and decodes Base64 data.
It belongs to GNU coreutils, the standard user-space utilities of most Linux systems.

## Selection rationale

- The track represents the classic Unix utility: a small C program with a documented CLI.
- The byte transform is deterministic. Each output byte is checkable.
- Coreutils ships upstream test vectors. They give an independent oracle after the source reveal.
- The program is small. The track serves as the baseline for the full skill workflow.

## Reference build

- Binary: `gbase64` from the Homebrew coreutils 9.12 bottle for macOS arm64.
- Homebrew built the binary. The evaluation does not control its flags.
- Metadata audit: 173 defined symbols remain. The audit finds no source file paths.
- A future revision can rebuild the binary with `eval/build.py` and the hardened profile.

## Oracle

- Byte-exact stdout, stderr, exit status, and files for challenge cases.
- After the source reveal: 201 upstream coreutils vectors run against both executables.

## Scope

- The scope is the full product. Rustify always targets a complete one-to-one reconstruction.
- The scorer measures the features that its cases cover. A feature without a case stays in scope.
- A failed or missing feature is a skill defect. The fix goes into the skills, not into a narrower scope.
- The full product covers every option, input mode, error message, and exit status of `base64`.
- The track needs no source-assisted repair.
- `run.py` scores a project in `work/projects/base64` and writes reports to `work/evaluation/base64/`.
