# Source-assisted native-dialog fidelity design

The scoped implementation preserves the original OS script and process-replacement boundary.
Rust constructs the original operation, text, and option data with serde_json.
The program encodes that data as a JSON literal and escapes Unicode line and paragraph separators.
Rust writes the program and embedded `assets/dialog.js` into an anonymous tempfile and rewinds it.
The Unix command exec replaces Rust with `/usr/bin/osascript -l JavaScript`.
The command clears its environment and suppresses stderr to follow the original CLI path.
The top-level script activates currentApplication and uses standard additions.
Standard C imports provide cancellation and exit behavior, as the original template does.
The script uses no AppKit bindings or System Events automation.

Entry uses displayDialog with a title and default answer.
The contracted Question and Info modes use displayAlert.
The native script directly supplies stdout and exit status.
Five pure tests cover parsing, original option data, safe JSON text, Unicode separators, and anonymous-file contents.
The tempfile dependency provides safe anonymous script-file ownership.

The first JXA child-process stage passed process results but failed Info focus.
The current exec stage has five fresh source-bound CUA cases.
Four raw image pairs are identical.
The entry acceptance pair retains a disclosed external pointer effect.
The original, failed-child, and current source pins remain separate.
Full zenity product parity remains unestablished.
