# textutil track

## Product

`textutil` is the macOS tool that converts documents between plain text, HTML, RTF, RTFD, Word, OpenDocument, and web archive formats.
It also prints document information and concatenates documents.
Apple ships it with every Mac. Apple does not publish its source.

## Selection rationale

- The track adds a closed-source document converter. The memorization risk is low.
- Users want an open version. No Linux tool reproduces its exact conversions.
- The binary is a thin front end. The closed AppKit text system does most of the work.
  The track therefore tests framework closure at a large scale: the Rust program must implement the format readers and writers.
- The output formats are text-based for the core scope. Exact comparison is possible.

## Reference

- Binary: `/usr/bin/textutil` from macOS 26.7.2 (build `25G325`), arm64e slice of a universal binary.
- `reference.yaml` pins the path, the SHA-256, and the operating system build.
- Metadata audit: the binary keeps 6 defined symbols. Objective-C class and selector names remain.
- The repository does not store the binary.

## Oracle

- `documents.py` generates every input format in Python from the public specifications: RTF 1.9.1, HTML 4.01, RTFD, MS-DOC with MS-CFB, ECMA-376, OpenDocument 1.2, WordprocessingML 2003, and WebKit web archives.
- `cases.py` defines the cases. Each case id is `<feature-id>/<case-name>` with a feature from `grading.yaml`.
- `run.py` replays each case in a fresh folder on both programs and compares the view.
  A case can have several steps in one folder, for example a round trip.
- `parsers.py` checks each output with independent parsers: an RTF tokenizer, `html.parser`, `zipfile` with an XML parser, `plistlib`, and an MS-CFB reader.
- The evaluator wrote the cases from the manual page, the help text, the binary strings, and observed behavior, without the agent's work.

## Reports

| Report | Class | Content |
| --- | --- | --- |
| `surface-manual` | `D-surface` | Help, manual examples, every error message, every option twice and without a value, `-noversion`. |
| `replay-core` | `D-replay` | `txt` and `rtf`, `-info`, `-cat`, `-stdin`, `-stdout`, `-output`, `-extension`, `--`, encodings, `-format`, fonts. |
| `replay-html` | `D-replay` | HTML input and output, images, and every HTML option. |
| `replay-archive` | `D-replay` | Every input format to every output format, `-info`, `-cat`, and standard input for each format. |
| `replay-metadata` | `D-replay` | Every metadata option for every output format, `-strip`, and metadata copy from inputs. |
| `metamorphic-roundtrip` | `D-metamorphic` | `txt` to each format and back, and `rtf` chains through format pairs. LF text with a final newline must survive each `txt` round trip. |
| `generate-options` | `D-generate` | 240 seeded probes over commands, input formats, options, and option combinations. |
| `parse-outputs` | Independent parsers | Each candidate output document must parse. |
| `repeatability` | Control | Two more reference runs per case must give the same view. |

The scorer also checks two controls: a wrong-output script and a script that calls `/usr/bin/textutil` must fail.

## View and variable fields

- The view is the exit status, standard output, standard error, and each file in the case folder with its bytes and permission bits.
- `HOME` is the case folder, so the view also contains files that the program writes under `HOME`.
- A sandbox denies each program exec except the program itself and `/bin/sh`, `/bin/bash`, and `/bin/dash` for the control scripts.
  A Rust program therefore cannot delegate a conversion to `/usr/bin/textutil` or another tool.
- The scorer replaces only these variable fields. Each rule accepts a value only inside the time window of the run.
  - Zip entry times in `docx` and `odt` files: the reference writes the wall clock in the `TZ` zone. Evidence: two runs 4 seconds apart differ only at these fields.
  - The `NSURLResponse` time in each web archive subresource: an archived CFAbsoluteTime. Evidence: two runs differ only at this double.
  - `NSLog` prefixes on standard error: the wall clock, the process id, and the thread id. Evidence: `-encoding 999` with HTML output.
  - Call-stack addresses after an uncaught exception, for example `-keywords "a, b"`: ASLR moves them in each run.
- Small `-timeout` values make HTML loads depend on the host load. The cases use only `0`, `20`, and `60`.
- The `SimpleText format` input type needs a resource fork. The cases do not cover it yet.

## Scope

- The scope is the full product. Rustify always targets a complete one-to-one reconstruction.
- The scorer measures the features that its cases cover. A feature without a case stays in scope.
- A failed or missing feature is a skill defect. The fix goes into the skills, not into a narrower scope.
- The full product covers every command and option, and every format: `txt`, `html`, `rtf`, `rtfd`, `doc`, `docx`, `wordml`, `odt`, and `webarchive`.
- The Rust program must not link AppKit, Foundation, WebKit, or CoreText for conversions.
- `run.py` scores a project in `work/projects/textutil` and writes reports to `work/evaluation/textutil/`.
- `grading.yaml` has lower confidence than a source-based grading. The component patterns come from the evaluator's reverse engineering.
