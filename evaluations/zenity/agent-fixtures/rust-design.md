# Source-assisted dialog fidelity design

The scoped implementation preserves the original OS script boundary.
The Rust parser constructs a JSON parameter value.
The Rust process starts `/usr/bin/osascript -l JavaScript - JSON` without a shell.
The embedded `assets/dialog.js` program reads JSON from its argument.
The script uses `Application.currentApplication()` and standard additions.
The script uses no System Events automation or AppKit bindings.
Entry uses `displayDialog` with `withTitle` and `defaultAnswer`.
The scoped CLI Question and Info modes use `displayAlert` with the title as alert text and the body as message.
The CLI supplies Yes and No labels for Question, so the original selects its alert path.
The script returns a JSON tuple containing acceptance and text.
Rust maps that tuple to the original stdout and status contract.
Quotes, Unicode, and script-looking strings remain data arguments.

The implementation uses serde_json and the Rust standard library.
Pure unit tests cover parsing and the JSON transport protocol without opening a dialog.
The five unit tests cannot prove current GUI appearance or behavior.
Fresh host-native replay must establish the five scoped workflows.
The previous AppKit captures remain historical evidence only.
The new source pin remains separate from the original freeze.
Full zenity product parity remains unestablished.
