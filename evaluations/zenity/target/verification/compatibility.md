# Verified five-workflow native-dialog smoke

The source-assisted exec candidate passes the five contracted workflows.
The parent performs the fresh host-native CUA replay.
The verifier checks the recorded proof without opening dialogs.
Full zenity product parity remains unestablished.

| Check | Result |
| --- | --- |
| Original and candidate process results | All ten results match the independent `recovered/tests.json` expectations. |
| Native family, title, icon, controls, and focus | The parent reviews and passes all five pairs. |
| Expected buttons | All ten AX captures match the declared button labels and counts. |
| Raw screenshot pairs | Four pairs have identical bytes. |
| Entry acceptance screenshot | The external pointer effect differs within `[192, 80, 225, 113]`. The controls and focus match. |
| Fresh Rust tests | Five pure tests pass. |
| Proof integrity tests | Eight tests pass, including missing, stale, failed-focus, raw-hash, declared-button, and checkpoint-failure cases. |
| Formatting, clippy, and release build | All checks pass. |
| Project checkpoints | All five checkpoints are current after proof verification. |

The raw images and AX captures remain unchanged under `../recovered/evidence/jxa-exec-replay/`.
`fresh-proof.json` preserves their hashes and the manual visual verdicts.
The screenshot filenames end in `.png`, but the capture tool supplies JPEG bytes.
The verifier detects that format and preserves the original bytes without conversion.
The pointer difference is a disclosed external capture artifact.
The verifier does not mask pixels or normalize application appearance.
The Info dialog now has the same active blue OK button and background as the original.

## Execution-model repair

The first source-assisted JXA candidate spawns an osascript child and waits.
Its five process results pass, but its Info dialog fails focus and appearance parity.
The failed stage and its captures remain in `../recovered/evidence/jxa-child-focus-failure.zip`.
The original CLI replaces itself with osascript.
The current Rust candidate now uses the same Unix exec boundary, an anonymous script file, and top-level activation.
The script uses currentApplication standard additions for the dialogs.
Standard C imports supply the original cancellation and process-status behavior.
The implementation uses no AppKit bindings or System Events automation.

The code budget includes tests.
The current implementation has 172 Rust lines and 14 JavaScript lines.
The total equals the former 186 Rust lines.
The repair adds 104 Rust lines and 14 JavaScript lines and removes 118 Rust lines.

## Preserved stages and source pins

The original binary-only freeze and recording archive remain unchanged.
The historical operational-state exception remains disclosed in provenance.
The first JXA pin, `../recovered/evidence/jxa-source-pin.json`, remains immutable.
The current pin, `../recovered/evidence/jxa-exec-source-pin.json`, also remains immutable.
Its pending label describes its creation before replay.
The later successful replay result belongs in this report and `fresh-proof.json`.
Historical AppKit or failed-child captures do not prove current-source acceptance.

## Limits and reproduction

The scope contains Entry accept/cancel, Question Yes/No, and Info OK on this macOS host.
Other dialog modes, options, platforms, timeouts, and complete product mappings remain outside this smoke.
The reference metadata marks its source tree as dirty, so the tag does not establish exact build-source identity.
The upstream interactive suite is not executed.

The user runs `python3 /path/to/rustify/evaluations/zenity/run.py` from any directory.
The default verifier consumes the preserved current-source proof.
The user can import a new batch with `--fresh-evidence DIRECTORY`.
The verifier requires matching source pins, executable hashes, raw hashes, original expectations, and a complete manual visual verdict before it advances checkpoints.
The verifier itself performs no GUI replay.

## Reproducible replay build

The replay executable uses Homebrew Rust 1.95.0 (`59807616e`) and Cargo 1.95.0.
The runner selects `/opt/homebrew/bin/cargo`, rustc, rustdoc, and Cargo plugins explicitly.
The local flags select `/usr/bin/clang` and `/usr/bin/ld`.
The runner clears inherited encoded flags, target-directory, SDK, deployment-target, and compiler-wrapper overrides.
`build-environment.json` records the compiler, linker, and SDK details.
The command records also identify each selected executable and build environment.
An inherited rustup Rust 1.94.0 compiler produces different bytes from the same source.
The verifier rejects those bytes as live GUI proof.
Both immutable source pins remain unchanged.
