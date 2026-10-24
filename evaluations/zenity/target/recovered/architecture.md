# Original architecture and current fidelity mapping

The reference executable contains Go build metadata for `github.com/ncruces/zenity/cmd/zenity`.
REA observes `CGO_ENABLED=0` and a dirty source-tree marker.
The original Question captures expose an osascript alert image.
These observations suggested an OS script boundary before source review.
The later tag review confirms that boundary without establishing the dirty binary's exact source identity.

## Original tag boundary

The original CLI builds dialog data and renders a JavaScript template.
`internal/zenutil/run_darwin.go::Run` invokes `osascript -l JavaScript`.
The script uses currentApplication standard additions to show native dialogs.
Entry selects `displayDialog` with a title and default answer.
The scoped CLI Question and Info flows select `displayAlert`.
The CLI supplies the Yes and No labels that select the Question alert path.

## Current Rust boundary

The current path is Rust options -> JSON parameter argument -> embedded `assets/dialog.js` -> osascript -> currentApplication standard additions -> native dialog.
The script returns a JSON acceptance-and-text tuple.
Rust maps cancellation and accepted entry text to the original CLI result contract.
The implementation uses no direct AppKit bindings or System Events automation.
The current source pin is `evidence/jxa-source-pin.json`.
The historical direct-AppKit implementation remains in the preserved archives.

## Open proof gaps

Fresh GUI proof is pending for all five workflows.
The old recordings do not validate the new source.
The Rust parent waits for its child; the original CLI can replace its own process with osascript.
Complete process-lifecycle, signal, option, and product parity remain unestablished.
`roadmap.md` records the current parity backlog.
