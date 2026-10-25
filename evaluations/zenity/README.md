# zenity track

## Product

This `zenity` is a cross-platform Go port of the GNOME zenity dialog tool.
Scripts use it to show native dialogs and read the user's answer.

## Selection rationale

- The track adds a desktop GUI program and a Go-compiled binary to the dataset.
- The agent must drive native macOS dialogs and capture their states.
- The process exit status and stdout give an exact oracle for each dialog action.

## Reference build

- Binary: `zenity_macos.zip` from the v0.10.15 GitHub release. The replay uses the arm64 slice of the universal binary.
- The upstream release controls the flags.
- Metadata audit: the binary has no defined symbols. Go still keeps type names, package paths, and function names in its runtime tables. The strings contain 766 such matches. Stripping cannot remove this metadata from a Go binary.

## Oracle

- Recorded GUI captures for entry acceptance, entry cancellation, question choices, and information acknowledgement.
- After the source reveal: a mapping of the scenarios to the upstream interactive tests. The upstream suite does not run.

## Scope and limits

- The track is a smoke test. It is not an independent full reconstruction.
- The default replay checks recorded evidence and fresh Rust unit tests. It does not perform a fresh native replay.
- The first evaluation run needed source-assisted repairs. The Git history before commit `ce882f1` keeps that run.
