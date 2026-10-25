# Source-bound host-native GUI replay

The parent performs native CUA interactions.
The verifier opens no dialogs.
The current five-case exec replay passes.
Full-product parity remains unestablished.

The executable is `../implementation/target/release/zenity`.
The immutable pin is `../recovered/evidence/jxa-exec-source-pin.json`.
The earlier `jxa-source-pin.json` belongs to the failed child stage and stays unchanged.
The exact arguments and expectations are in `recovered/scenarios.json` and `recovered/tests.json`.

## Capture convention

Each workflow uses `entry-accept`, `entry-cancel`, `question-accept`, `question-cancel`, or `info-accept`.
Each role uses `reference` or `candidate`.
The files are `{id}-{role}.json`, `{id}-{role}-ax.txt`, and `{id}-{role}.png`.
The tool supplies JPEG image bytes under those original filenames.
The verifier preserves the raw bytes.

Each process record contains `case: {id, args}`, `executable_sha256`, `captured_at_utc`, `capture_method: "host-native CUA"`, `returncode`, `stdout_b64`, and `stderr_b64`.
The record also contains `ax_file`, `ax_sha256`, `screenshot_file`, and `screenshot_sha256`.
Candidate records include the current `source_pin_sha256`.
Every timestamp follows pin creation.

The visual-review.json file identifies that source pin and the CUA method.
Its cases object contains all five IDs.
Each case requires passed status, focus, title, icon, family, and controls verdicts.
Entry acceptance may disclose an external pointer effect.
No other unexplained raw image difference passes.
The verifier never alters images or normalizes application appearance.

## Actions and verification

The parent verifies copied executable hashes before using app wrappers.
The parent captures both dialogs before each action closes them.
Entry acceptance replaces seed with `Rustify GUI test` and presses OK.
Entry cancellation presses Cancel.
Question acceptance presses Yes, and cancellation presses No.
Info acceptance presses OK.
The parent records actual process results and preserves failures even when process results pass.
A code change needs a new pin and a separate replay stage.

The verifier imports a completed batch with:

```sh
python3 evaluations/zenity/run.py --fresh-evidence /absolute/capture/directory
```

The default command checks `recovered/evidence/jxa-exec-replay/`.
It consumes tests.json expectations, raw hashes, source identities, timestamps, and manual verdicts.
It advances checkpoints only after those checks pass.
Missing, stale, altered, or failed proof cannot pass.
The proof tests also verify that a checkpoint failure cannot return success.

The current proof has four byte-identical image pairs.
Entry acceptance has the disclosed external pointer effect within `[192, 80, 225, 113]`.
The current Info focus and appearance match the original.
