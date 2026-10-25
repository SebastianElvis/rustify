# Source audit and verified exec-boundary repair

The current source-assisted candidate passes the five recorded native workflows.
Fresh CUA proof binds to the immutable exec-stage source pin.
Five pure Rust tests and eight proof-integrity tests pass without opening dialogs.
Full zenity product parity remains unestablished.

## Original identity and boundary

The audit uses the official `ncruces/zenity` tag `v0.10.15`.
The archive hash is `ed900c7f0a16976fa57c06000f4a9e06e65dce669a475f54d52ddc2b77027e24`.
`../recovered/evidence/original-zenity-v0.10.15.tar.gz` preserves the source.
The reference's Go metadata marks its source as dirty.
The tag cannot establish that binary's exact source identity.

| Original component | Current implementation | Evidence and limit |
| --- | --- | --- |
| CLI `loadFlags` | Rust `parse` and `parameters` | The five cases preserve their original inputs and button defaults. The full CLI remains outside this smoke. |
| `entry_darwin.go::entry` | Entry parameter data and `assets/dialog.js` | Both paths select displayDialog with title and default answer. Both fresh Entry cases pass. |
| `msg_darwin.go::message` and CLI labels | Question and Info parameter data | The CLI supplies Yes/No labels, so both message modes use displayAlert. Three fresh alert cases pass. |
| `util_darwin.go::getButtons` | Button arrays and default/cancel indexes | The verifier checks every AX capture against tests.json. The parent reviews controls and focus. |
| `internal/zenutil/run_darwin.go::Run` | Anonymous `script_file` and CommandExt::exec | Both paths replace the command process with osascript. Rust no longer waits for a child. |
| `osascripts/common.gojs` | Top-level currentApplication activation | The fresh Info alert has the same active blue OK button and background. |
| `osascripts/dialog.gojs` | Top-level result and status handling | Standard C imports supply cancellation and exit codes. The native script supplies stdout directly. All ten process results pass. |

Rust encodes JSON data and escapes Unicode line and paragraph separators before script compilation.
The tempfile dependency supplies safe anonymous-file ownership.
The implementation uses no AppKit bindings or System Events automation.
The command clears its environment and routes stderr to null, following the original empty environment and closed stderr boundary.
This smoke does not establish every failure, signal, or fallback-exec behavior.

## Preserved stages

The original direct-AppKit stage remains in the historical freeze and recording archive.
The first JXA stage spawns osascript and leaves a Rust parent waiting.
Its five process results pass, but its Info dialog has inactive gray controls and background.
An icon click does not resolve that mismatch.
`../recovered/evidence/jxa-child-focus-failure.zip` preserves the failed stage, source, pin, and captures.
The old pin remains unchanged at `../recovered/evidence/jxa-source-pin.json`.

The exec repair restores process replacement and top-level script activation.
Its immutable pin is `../recovered/evidence/jxa-exec-source-pin.json`.
The pin's pending label records its creation before replay.
The later successful result belongs in `fresh-proof.json` and `comparison.json`.
The code contains 172 Rust lines and 14 JavaScript lines, including tests.
The repair adds 104 Rust lines and 14 JavaScript lines and removes 118 Rust lines.
The total remains at the former 186-line budget.

## Fresh proof and limits

`../recovered/evidence/jxa-exec-replay/` preserves all raw process, AX, and image records.
The verifier consumes original-derived process expectations and buttons from tests.json.
It checks executable hashes, source pins, capture times, raw hashes, and all manual visual verdicts.
The verdicts cover focus, title, icon, family, and controls for every case.
Four screenshot pairs have identical raw bytes.
Entry acceptance differs only in the external pointer effect within `[192, 80, 225, 113]`.
Both raw images remain unchanged, and the report discloses that difference.
The tool supplies JPEG bytes under `.png` filenames; the verifier detects the format without transcoding.
Hashes establish file integrity rather than capture authenticity.
The parent supplies the trusted CUA observations and visual review.

The upstream interactive suite is not executed.
Other modes, options, platforms, timeouts, and full-product mappings remain open.
The historical archive has 37 matching non-state frozen files.
The original frozen state snapshot is unavailable after the parent's later operational checkpoint.
The preserved later state and its different hash remain disclosed in provenance.
That exception does not authorize acceptance for different source.
