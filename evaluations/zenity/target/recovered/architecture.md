# Original architecture and current fidelity mapping

The reference contains Go build metadata for `github.com/ncruces/zenity/cmd/zenity`.
REA observes `CGO_ENABLED=0` and a dirty source-tree marker.
The original captures expose an osascript alert image.
These observations suggested an OS script boundary before source review.
The tag review confirms that boundary without establishing the dirty binary's exact source identity.

## Original and current boundaries

The original CLI constructs dialog data and renders a JavaScript program.
Its command path writes an unlinked script file and replaces itself with `osascript -l JavaScript`.
The program activates currentApplication and uses standard additions for native dialogs.
Entry selects `displayDialog` with a title and default answer.
The scoped CLI Question and Info flows select `displayAlert`.

The current Rust path is options -> safe JSON data -> anonymous script file -> Unix exec -> top-level JXA activation -> native standard-additions dialog.
The script supplies the original process cancellation and output behavior.
The Rust implementation no longer waits for an osascript child.
It uses no AppKit bindings or System Events automation.
`tempfile` supplies the anonymous file, and serde_json supplies the data encoding.
The JSON transport escapes Unicode line and paragraph separators before script compilation.

## Stage evidence and limits

The first JXA child-process stage fails Info focus despite matching all five process results.
`evidence/jxa-child-focus-failure.zip` preserves that distinct failed stage.
The exec-stage proof passes all five workflows and is stored in `evidence/jxa-exec-replay/`.
The current immutable source pin is `evidence/jxa-exec-source-pin.json`.
The first JXA pin and historical AppKit freeze remain unchanged.
The original tag and current scoped Rust architecture now share the OS script and process-replacement boundary.
Complete signal, option, platform, and product parity remain unestablished.
