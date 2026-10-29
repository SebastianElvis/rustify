# Open-source repository

The user publishes only `implementation/` as an open-source repository.
`recovered/` and `verification/` stay private working records.
The agent completes these files during implementation. No separate release phase exists.

## Self-containment

No file under `implementation/` links to or reads a path outside `implementation/`.
Every test runs without the original and without `recovered/`.
Each acceptance test keeps its expected result as a YAML fixture under `implementation/tests/fixtures/`.
Documents name requirement and component identifiers as plain text, not as links.

## Required files

| File | Content |
| --- | --- |
| `README.md` | The content of [the README template](../assets/README.md). |
| `LICENSE` | The full text of the license in the `license` field. The user selects the license. The default is `MIT`. |
| `CHANGELOG.md` | [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/) format with [Semantic Versioning 2.0.0](https://semver.org/). The first version is `0.1.0`. |
| `CONTRIBUTING.md` | The build, test, and check commands. The rule that a change keeps original behavior. The rule that a known difference goes into `docs/compatibility.md`. |
| `SECURITY.md` | The supported versions and the GitHub private vulnerability reporting channel. |
| `CODE_OF_CONDUCT.md` | The [Contributor Covenant 2.1](https://www.contributor-covenant.org/version/2/1/code_of_conduct/) by reference, and its report channel. |
| `docs/design.md` and `docs/adr/` | The design and the decision records from planning. |
| `docs/migration.md` | The replacement of the original: installation, executable names, configuration and data paths, environment variables, and the return to the original. |
| `docs/compatibility.md` | The compatibility document that `rustify-validate` writes. |
| `.github/workflows/ci.yml` | The content of [the CI template](../assets/ci.yml). |
| `.github/workflows/release.yml` | The content of [the release template](../assets/release.yml). |

The README does not copy results from `docs/compatibility.md`. A validation result does not change implementation inputs.
The agent replaces each `{{PLACEHOLDER}}` in a template.
Each release target has `os`, `target`, and `ext` values for each platform of the original.
The agent does not push, tag, or publish the repository.

## Package metadata

`Cargo.toml` sets `description`, `license`, and `rust-version` in `[package]`.
It sets `repository` and `homepage` only when the user supplies them.
The `rust-version` is the oldest toolchain that passes the CI `msrv` job.

## Rustdoc

- Each crate root starts with a `//!` summary and `#![warn(missing_docs)]`.
- Each module starts with a `//!` comment. The comment states the module responsibility and its original component identifier.
- Each public item has a doc comment. Each public function of a library crate has a runnable example.
- The `check` command runs `cargo doc` with `RUSTDOCFLAGS="-D warnings"`. CI runs the same command.

## Tests

| Kind | Location | Rule |
| --- | --- | --- |
| Unit | `#[cfg(test)]` modules | The inner loop of the slice workflow writes them. |
| Acceptance | `tests/` | Each test runs the built executable through its real interface. Its name contains its `TEST` identifier. |
| Property | `tests/` with [proptest](https://docs.rs/proptest/latest/proptest/) | One property for each round trip, invariant, or metamorphic relation in the requirements. The agent keeps `proptest-regressions/`. |
| Documentation | Doc comments | `cargo test` runs them. |
| Fuzz | `fuzz/` with [cargo-fuzz](https://rust-fuzz.github.io/book/cargo-fuzz.html) | One target for each parser of external input. |

The agent runs each fuzz target for 60 seconds when `cargo-fuzz` and a nightly toolchain are installed.
A fuzz crash is a gap with the crash input as its reproducer.
The agent runs `check --coverage` when `cargo-llvm-cov` is installed. The `check` command records line and region coverage.
