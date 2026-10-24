# Desktop source audit and JXA fidelity repair

The current implementation uses the original OS script boundary.
This SOURCE-ASSISTED repair still requires fresh GUI replay.
Five pure unit tests pass, but no current GUI workflow has completed.
Full zenity product parity remains unestablished.

## Original source identity

The audit uses the official `ncruces/zenity` tag `v0.10.15`.
`../recovered/provenance.json` records the source and release hashes.
The source archive SHA-256 is `ed900c7f0a16976fa57c06000f4a9e06e65dce669a475f54d52ddc2b77027e24`.
The archive is preserved in `../recovered/evidence/original-zenity-v0.10.15.tar.gz`.
The reference binary's Go metadata marks its source tree as dirty.
The tag therefore cannot establish the exact source of the reference binary.
The source audit preserves that identity limitation.

## Original-to-Rust component mapping

| Original source component | Current implementation | Fidelity status |
| --- | --- | --- |
| `cmd/zenity/main.go::loadFlags` | `src/main.rs::parse` | The five cases preserve their Entry, Question, Info, title, text, and entry-value inputs. Full CLI parity remains outside this smoke. |
| `entry_darwin.go::entry` | The Entry branch in `assets/dialog.js` | Both paths select `displayDialog` with `withTitle` and `defaultAnswer`. Fresh native-control and appearance checks remain pending. |
| `msg_darwin.go::message` and CLI `loadFlags` | The Question and Info branches in `assets/dialog.js` | The CLI supplies Question Yes/No labels. The original therefore selects `displayAlert`, as the current script does. Info also uses `displayAlert`. |
| `util_darwin.go::getButtons` | The script's buttons, defaultButton, and cancelButton values | Entry uses Cancel/OK, Question uses No/Yes, and Info uses OK. Fresh button and focus checks remain pending. |
| `internal/zenutil/osascripts/common.gojs` | The script's currentApplication and standard-additions setup | Both paths use the native OS script host. The current script uses no System Events automation or direct AppKit bindings. |
| `internal/zenutil/run_darwin.go::Run` | `src/main.rs::show` | Both paths invoke `osascript -l JavaScript`. Rust passes safe JSON argument data and reads a JSON result. Complete process-lifecycle parity remains unestablished. |
| `cmd/zenity/main.go::strResult` and `errResult` | `src/main.rs::outcome` | Pure tests cover accepted text, newlines, empty output, and cancellation. The five actual GUI process results still require fresh captures. |

The current path is Rust options -> JSON argument -> embedded JavaScript asset -> osascript -> currentApplication standard additions -> native dialog.
The script returns a JSON acceptance-and-text tuple to Rust.
Rust maps that tuple to stdout and exit status.
The original CLI can replace its process with osascript, while the Rust implementation waits for its child.
The five-workflow smoke does not establish complete signal or process-lifecycle parity.

## Repair provenance and code budget

The original freeze precedes source review.
The historical candidate used direct objc2 AppKit bindings.
That earlier design introduced avoidable native-family, icon, and title-placement differences.
The current repair removes the bindings and preserves the revealed JXA boundary.
`jxa-fidelity.patch` records the source-assisted change.

The code budget includes unit tests.
The repair adds 89 Rust lines and 22 JavaScript lines and removes 111 Rust lines.
The current code has 164 Rust lines and 22 JavaScript lines.
The former code has 186 Rust lines.
The five current tests preserve the useful result assertions and add safe JSON protocol checks.
They do not open a dialog.

`../recovered/evidence/pre-jxa-repair.zip` preserves the prior implementation, models, reports, and operational state.
`../recovered/evidence/jxa-source-pin.json` pins the new source and release executable separately from the historical freeze.
The current pin remains immutable after replay starts.
The historical freeze and recording archive remain unchanged.

## GUI proof and scope

The old five recordings describe the historical AppKit candidate only.
They do not prove current-source GUI parity.
The Mac was locked during the fresh replay preflight.
No current Entry, Question, or Info workflow has completed.
The current verifier reports `pending_fresh_gui_replay` and does not advance candidate checkpoints.
Fresh CUA captures must bind to the current source pin and executable hash.
The parent must compare native family, title presentation, default icon, controls, focus, and process results.
The earlier visual allowances do not establish current acceptance.

The related upstream tests are `entry_test.go::TestEntry_script` and `msg_test.go::TestMessage_script`.
The library's extra-button No result differs from CLI cancellation.
The smoke does not claim that it runs those upstream tests.
Other dialog modes, options, platforms, timeouts, and full-product mappings remain open gaps.

## Historical state exception

The historical archive contains 37 matching non-state frozen files.
The parent changed operational state after the original freeze.
The original state snapshot is unavailable.
The preserved later snapshot and its distinct hash remain disclosed in provenance.
This historical exception does not authorize current-source GUI claims.
