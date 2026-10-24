# Fresh host-native replay for the JXA candidate

The current verifier runs no GUI automation.
The parent performs fresh CUA replay after the Mac is unlocked.
The historical AppKit captures cannot establish current parity.

The current candidate is `../implementation/target/release/zenity`.
The exact cases and source-pin hash are in `work/strict-zenity/replay-cases.json` under the repository root.
The immutable source pin is `../recovered/evidence/jxa-source-pin.json`.
The parent verifies copied executable hashes before using app wrappers.

## Capture convention

The parent writes captures under `work/strict-zenity/evidence/`.
Each case uses `entry-accept`, `entry-cancel`, `question-accept`, `question-cancel`, or `info-accept` as its identifier.
Each executable uses `reference` or `candidate` as its role.
The file names are `{id}-{role}.json`, `{id}-{role}-ax.txt`, and `{id}-{role}.png`.

Each process JSON contains these fields.

```json
{
  "case": {"id": "entry-accept", "args": ["the exact recorded case arguments"]},
  "executable_sha256": "the actual executed binary hash",
  "source_pin_sha256": "the current pin-file hash; this field is required for candidate captures",
  "capture_method": "host-native CUA",
  "captured_at_utc": "the actual UTC capture time",
  "returncode": 0,
  "stdout_b64": "the actual stdout bytes in base64",
  "stderr_b64": "the actual stderr bytes in base64",
  "ax_file": "entry-accept-candidate-ax.txt",
  "screenshot_file": "entry-accept-candidate.png",
  "visual_parity": "passed only after the parent compares both native dialogs"
}
```

The parent copies actual values into every field.
The example strings do not constitute proof.
The parent records `visual_parity: "passed"` only after it checks native family, title, icon, controls, and focus.
The parent preserves failed and incomplete results.
The parent does not record a completed workflow while the session is locked.
The source pin stays unchanged throughout a replay batch.

## Actions and expected results

| Case | Native family and controls | Action | Independent expected result |
| --- | --- | --- | --- |
| Entry accept | `displayDialog`, the title, the message, seed text, OK, and Cancel | The parent replaces seed with `Rustify GUI test` and presses OK. | Status 0, stdout `Rustify GUI test` plus a newline, and empty stderr. |
| Entry cancel | The same entry controls | The parent presses Cancel. | Status 1 and empty stdout and stderr. |
| Question accept | `displayAlert`, the title as alert text, the message, Yes, and No | The parent presses Yes. | Status 0 and empty stdout and stderr. |
| Question cancel | The same Question controls | The parent presses No. | Status 1 and empty stdout and stderr. |
| Info accept | `displayAlert`, the title as alert text, the message, and OK | The parent presses OK. | Status 0 and empty stdout and stderr. |

The parent runs both pinned executables with each case's arguments.
The parent uses fresh AX and image captures before the action closes each dialog.
A later verification step must check all five current-source workflows before it can advance the candidate's state.
The current runner intentionally remains pending until that fresh proof is supplied and verified.
