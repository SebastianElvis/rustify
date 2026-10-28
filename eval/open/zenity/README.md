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
- License: zenity uses MIT.

## Oracle

- Recorded GUI captures for entry acceptance, entry cancellation, question choices, and information acknowledgement.
- After the source reveal: a mapping of the scenarios to the upstream interactive tests. The upstream suite does not run.

## Scope

- The scope is the full product. Rustify always targets a complete one-to-one reconstruction.
- The scorer measures the features that its cases cover. A feature without a case stays in scope.
- A failed or missing feature is a skill defect. The fix goes into the skills, not into a narrower scope.
- The full product covers every dialog type and option of this `zenity`, including entry, question, information, warning, error, file selection, list, progress, scale, color, calendar, notification, password, and forms.
- The current scorer replays five recorded GUI cases. This coverage is too small and needs new cases.
- The first evaluation run needed source-assisted repairs. The Git history before commit `ce882f1` keeps that run.
- `run.py` scores a project in `work/projects/zenity` and writes reports to `work/evaluation/zenity/`.
