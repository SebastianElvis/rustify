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

- `cases.py` writes every input itself: PNG images in all color types, bit depths, and interlace methods, BMP and TIFF images, and `.icns` containers with PNG, ARGB, and legacy entries.
- The `.car` inputs are four asset catalogs of the pinned macOS build. `cases.py` checks their SHA-256.
  `xcrun actool` cannot build a test catalog on the evaluation host: the Xcode first-launch step is missing.
- The component patterns come from binary analysis. Their confidence is lower than source-based grades.
- The case ids have the form `<feature-id>/<case-name>`. The feature ids come from `grading.yaml`.

| Report | Class | Content |
| --- | --- | --- |
| `replay-core` | D-replay | Usage, options, default names, full conversions, and errors. |
| `replay-sizes` | D-replay | Each icon size and scale, missing and extra files, and wrong dimensions. |
| `replay-images` | D-replay | PNG formats, PNG chunks, corrupt images, and non-PNG images. |
| `replay-legacy` | D-replay | Legacy, ARGB, and PNG entries, and corrupt `.icns` containers. |
| `replay-environment` | D-replay | `ICONCOMPILER_SEPARATE_HIDPI` and `ICONCOMPILER_GENERATE_BASE_SYSTEM_ICNS`. |
| `replay-catalog` | D-replay | Icon extraction from `.car` files and icon-name errors. |
| `surface-manual` | D-surface | One case for each claim of the manual page and the usage text. |
| `generate-random` | D-generate | 300 seeded probes over option forms, inputs, output names, and environment flags. |
| `metamorphic-roundtrip` | D-metamorphic | Multi-step round trips. PNG entries must not change in a second round trip. |
| `parsers-format` | Independent parsers | A checker from the public ICNS description and Pillow read each output file. |
| `repeatability` | Control | The reference against itself on all single-step cases. |

The scorer also runs a wrong executable. That control must fail.

## Variable output

Two self-tests of the reference, each with a repeatability pass, found two variable parts. `run.py` declares a rule for each part.

- `nslog-prefix`: an empty default output name makes Foundation print an `NSLog` line.
  The prefix holds the time, the process identifier, and the thread identifier. The rule removes only this prefix.
- `undefined-pixels`: the reference decodes PNG data in an `ic05` entry (32x32 pixels) or in an `icp6` entry as raw pixels.
  It reads past the entry data. Twelve runs give twelve different pixel sets.
  The rule compares only the file name and the PNG header for the three cases that `UNDEFINED` lists.
  The generator does not put PNG data into these two entry types.
- The output is otherwise byte-exact. The entry order in `.icns` files is stable across runs.

## Gaps

- The case format cannot set file modes or create symbolic links or empty folders. Permission errors have no case.
- `cases.py` has no JPEG or JPEG 2000 encoder. The cases use only JPEG and JPEG 2000 headers.
- The `icnsutils` clone is not installed on the evaluation host. It gives no second opinion yet.
- `run.py` does not run `D-adaptive` or binary-guided `D-coverage`.

## Scope

- The scope is the full product. Rustify always targets a complete one-to-one reconstruction.
- The scorer measures the features that its cases cover. A feature without a case stays in scope.
- A failed or missing feature is a skill defect. The fix goes into the skills, not into a narrower scope.
- The full product covers `-c icns`, `-c iconset`, `-o`, default output names, `.car` extraction, and every error.
- The Rust program must not link the feature libraries in `reference.yaml`.
- The observed catalog pipeline uses `CoreImage` for resize and composition. The track forbids `CoreImage`.
- The Rust program can use Metal for its own GPU kernel. The kernel must not load the original `CoreImage` code.
- `run.py` scores a project in `work/projects/iconutil` and writes reports to `work/evaluation/iconutil/`.
