# Recorded desktop smoke

The runner verifies five previously recorded native GUI workflows.
The runner does not perform a new live GUI replay.

| Workflow | Expected stdout | Expected status |
| --- | --- | --- |
| Entry accept | `Rustify GUI test` followed by a newline | 0 |
| Entry cancel | The output is empty. | 1 |
| Question Yes | The output is empty. | 0 |
| Question No | The output is empty. | 1 |
| Information OK | The output is empty. | 0 |

Every recorded stderr stream is empty.
The runner checks each executable's capture independently against these expectations.
The runner also checks the recorded code and evidence hashes.
The runner runs fresh formatting, Clippy, and four Rust unit tests.
These unit tests do not open dialogs.
`summary.json` distinguishes fresh unit checks from recorded GUI cases.

The parent uses actual host-native CUA for the original replay.
The entry screenshots preserve the entered value and buttons.
The question and information AX captures preserve text and button labels.
The contract permits icon, layout, and title-placement differences.
The runner does not compare screenshots as pixel-equivalent images.

The Go metadata reports a dirty source tree.
The original tag's exact build identity remains unknown.
The source audit confirms a Go script boundary and a different direct-AppKit Rust design.
The audit makes no source-assisted Rust change.
The parent fixes application initialization before the freeze through runtime feedback.

The parent updates operational state after the freeze.
The source audit discloses that state-only hash mismatch.
All frozen Rust source and GUI evidence hashes match.

The runner uses a command-local Darwin system-linker setting for this host.
The runner preserves an explicit `RUSTFLAGS` value.
The runner changes no global configuration.

The evaluator runs `python3 /path/to/rustify/evaluations/zenity/run.py`.
The runner accepts any working directory.
`GUI-REPLAY.md` describes a separate host-native live replay.
This track is a parent-run smoke. It does not claim independent or complete reconstruction.
