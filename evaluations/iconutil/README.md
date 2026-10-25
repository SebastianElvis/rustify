# iconutil track

## Product

`iconutil` is the macOS tool that converts between `.iconset` folders and `.icns` icon files.
It can also extract an icon from a compiled `.car` asset catalog.
Apple ships it with every Mac. Apple does not publish its source.

## Selection rationale

- The track adds a closed-source binary with no source to reveal. The memorization risk is low.
- Users want an open version. The Linux `icnsutils` package describes its `icnsutil` tool as a functional clone of Darwin's `iconutil`.
- The `.icns` format is a binary container with PNG and legacy bitmap entries. The output is deterministic and exactly checkable.
- The binary is small (about 136 KB) and stripped. It calls the closed IconServices, ImageIO, and Accelerate frameworks for its features.
- The track tests framework closure: the Rust program must implement the container and image handling itself.

## Reference

- Binary: `/usr/bin/iconutil` from macOS 26.7.2 (build `25G325`), arm64e slice of a universal binary.
- `reference.yaml` pins the path, the SHA-256, and the operating system build.
- Metadata audit: the binary keeps 6 defined symbols. Objective-C class and selector names remain.
- The repository does not store the binary.

## Oracle

- Black-box replay of `iconutil -c icns` and `iconutil -c iconset` with generated iconsets: all standard sizes, missing sizes, extra files, wrong dimensions, and corrupt PNG data.
- Byte-exact `.icns` output and exact `.iconset` file sets.
- Round trips: `.iconset` to `.icns` to `.iconset`.
- Independent parsers must read the `.icns` output.
- The `icnsutils` clone gives a second opinion on the format. The original binary decides.

## Scope

- The scope is the full product. Rustify always targets a complete one-to-one reconstruction.
- The scorer measures the features that its cases cover. A feature without a case stays in scope.
- A failed or missing feature is a skill defect. The fix goes into the skills, not into a narrower scope.
- The full product covers `-c icns`, `-c iconset`, `-o`, default output names, `.car` extraction, and every error.
- The Rust program must not link IconServices, ImageIO, CoreGraphics, or AppKit.
- `run.py` scores a project in `work/projects/iconutil` and writes reports to `work/evaluation/iconutil/`.
