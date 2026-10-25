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

- Black-box replay of `-info`, `-convert`, and `-cat` on generated documents.
- Byte-exact output for `txt`, `html`, and `rtf`, with the known variable parts (such as generator versions and dates) recorded.
- Cases from the manual page and the help text, written by an evaluator who does not see the agent's work.
- Round trips such as `txt` to `rtf` to `txt`.

## Scope

- The scope is the full product. Rustify always targets a complete one-to-one reconstruction.
- The scorer measures the features that its cases cover. A feature without a case stays in scope.
- A failed or missing feature is a skill defect. The fix goes into the skills, not into a narrower scope.
- The full product covers every command and option, and every format: `txt`, `html`, `rtf`, `rtfd`, `doc`, `docx`, `wordml`, `odt`, and `webarchive`.
- The Rust program must not link AppKit, Foundation, WebKit, or CoreText for conversions.
- `run.py` scores a project in `work/projects/textutil` and writes reports to `work/evaluation/textutil/`.
