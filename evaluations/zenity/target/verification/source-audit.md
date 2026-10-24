# Desktop smoke source audit

The parent freezes the Rust source and native replay evidence before source review.
The audit uses the official `ncruces/zenity` tag `v0.10.15`.
`../recovered/provenance.json` records its archive URL and SHA-256.

## Product, experience, and architecture

| Recovered claim | Tag source evidence | Audit result |
| --- | --- | --- |
| The CLI selects entry, question, and information dialogs. | `cmd/zenity/main.go::main`, `loadFlags` | The source confirms the selected dialog modes. |
| An accepted entry returns text with a newline. | `entry_darwin.go::entry`, `cmd/zenity/main.go::strResult` | The source supports the recorded accepted-entry result. |
| Cancellation returns status 1. | `cmd/zenity/main.go::errResult` | The source supports the recorded cancel result. |
| Questions have default Yes and No labels. | `cmd/zenity/main.go::loadFlags` | The source confirms these CLI defaults. |
| Entry dialogs contain a title, message, answer, and buttons. | `entry_darwin.go::entry` | The source fills the corresponding native-dialog fields. |
| Information dialogs contain a title, message, and OK button. | `msg_darwin.go::message`, `loadFlags` | The source supports the recorded controls. |
| The Go CLI delegates native dialogs through an OS script boundary. | `internal/zenutil/run_darwin.go::Run` | The source renders a template and runs `osascript -l JavaScript`. |

The original architecture has this flow:

```text
Go CLI -> Dialog data -> Script template -> osascript/JXA -> Native dialog
```

The Rust replacement has this flow:

```text
Rust options -> objc2 AppKit bindings -> NSAlert and NSTextField
```

The tag source confirms the inferred script boundary.
The replacement uses a different internal architecture.
The recorded binary metadata marks its source as dirty.
The tag cannot establish the exact source of that binary.
The audit therefore compares tag behavior and architecture with the recorded binary model.

## Upstream test mapping

| Recorded workflow | Related upstream behavior | Adaptation |
| --- | --- | --- |
| Entry acceptance | `entry_test.go::TestEntry_script` cases `123` and `abc` | The smoke uses `Rustify GUI test` and checks CLI output. |
| Entry cancellation | `entry_test.go::TestEntry_script/Cancel` | The smoke maps the cancellation result to CLI status 1. |
| Question Yes | `msg_test.go::TestMessage_script/QuestionYes` | The smoke uses the CLI's two default buttons. |
| Question No | `msg_test.go::TestMessage_script/QuestionNo` and CLI `loadFlags` | The library test uses an extra No button. The smoke uses the CLI's No cancel button. |
| Information OK | `msg_test.go::TestMessage_script/InfoOK` | The smoke checks CLI success and empty output. |

The upstream question test has an extra-button result distinct from cancellation.
The captured CLI No flow has empty stdout and status 1.
The audit does not treat these as identical test executions.
The upstream script tests require interactive dialogs.
This export does not execute those tests.
The runner verifies the parent's recorded evidence and runs fresh Rust unit tests.

## Corrections and limits

The parent corrects missing `NSApplication::finishLaunching` before the freeze.
The correction uses runtime feedback.
The audit makes no source-assisted Rust changes.
The smoke permits icon, title placement, and pixel-layout differences.
The parent checks semantic text, buttons, entered value, and process results.
The parent performs this GUI smoke without an independent reconstruction worker.
The export does not claim full zenity reconstruction or broad desktop compatibility.

## Freeze state exception

All 37 non-state frozen files still match their recorded hashes.
The parent checkpoints `state.json` after the freeze.
The original state snapshot is unavailable.
The export preserves the later state and discloses its different hash.
The source and GUI evidence have no hash exception.
