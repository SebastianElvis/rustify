# Source-assisted native-dialog fidelity repair

The current candidate requires fresh GUI replay.
The current desktop result is `pending_fresh_gui_replay`.
The Mac was locked during the parent's replay preflight.
No current GUI workflow has completed.

## Current non-GUI checks

Formatting, Clippy, five pure Rust unit tests, and the release build pass.
The unit tests check option parsing, button defaults, cancellation, Unicode, newlines, safe JSON parameters, and malformed script results.
These checks do not open dialogs or establish visual parity.
The verifier returns status 2 while fresh GUI proof is missing.
The verifier does not advance the current candidate's checkpoints.

## Historical evidence

The original freeze and `../recovered/evidence/frozen-recording.zip` remain unchanged.
The historical archive preserves the direct-AppKit candidate and its five GUI recordings.
`../recovered/evidence/pre-jxa-repair.zip` also preserves the previous implementation, models, state, and reports.
The disclosed post-freeze operational-state exception remains unchanged.
Historical AppKit captures do not validate the new JXA source.
The current report separates five historical cases from zero fresh cases.

## Repair

This SOURCE-ASSISTED repair follows the original-source review.
The Rust implementation now uses the original OS script boundary.
Rust passes JSON as a process argument and supplies an embedded JavaScript asset to `/usr/bin/osascript -l JavaScript`.
The script uses `Application.currentApplication()` and standard additions.
The script uses no System Events automation or direct AppKit bindings.
Entry uses `displayDialog` with its title and default answer.
The scoped Question and Info modes use `displayAlert` with the title as alert text and the dialog text as message.
The default Question controls are Yes and No.
The source confirms that the CLI supplies those labels and selects the alert path.

The complete code change includes unit tests.
It adds 89 Rust lines and 22 JavaScript lines and removes 111 Rust lines.
The current code has 164 Rust lines and 22 JavaScript lines.
The former implementation has 186 Rust lines.
The total code budget therefore does not grow.
`jxa-fidelity.patch` records the change.
`../recovered/evidence/jxa-source-pin.json` pins the new source and release executable separately from the historical freeze.
That pin remains immutable after replay starts.
Later replay results belong in separate reports.

## Scope and pending checks

The required workflows are entry acceptance, entry cancellation, Question Yes, Question No, and Info OK.
Fresh captures must bind to the new source pin and executable hash.
The parent must compare native dialog family, title presentation, default icon, controls, focus, and independent process results.
The prior icon and title-placement allowances no longer establish current acceptance.
The source tag still cannot establish the dirty reference binary's exact source identity.
Full zenity product parity remains unestablished.
Other modes, platforms, timeout behavior, and arbitrary CLI syntax remain outside this five-workflow smoke.
