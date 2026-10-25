# Recovered and verified native-dialog specification

The scope contains five original Entry, Question, and Info workflows.
Original reference observations define the expectations in `tests.json`.
The current exec candidate has fresh source-bound CUA proof for all five cases.

| Interface | Original and current native family | Title and text | Controls |
| --- | --- | --- | --- |
| Entry | JXA `displayDialog` | `withTitle` carries the title. The argument carries the message. `defaultAnswer` carries seed text. | OK and Cancel appear. Accepted text reaches stdout with a newline. |
| Question CLI defaults | JXA `displayAlert` | The alert argument carries the title. `message` carries the text. | Yes and No appear. No cancels with status 1. |
| Info | JXA `displayAlert` | The alert argument carries the title. `message` carries the text. | OK appears. Acceptance returns status 0 with empty output. |

The parent compares native family, title presentation, default icon, controls, and focus for every pair.
Four raw screenshot pairs match byte-for-byte.
Entry acceptance differs only in the external pointer effect within `[192, 80, 225, 113]`.
Both raw images remain intact, and the manual review confirms matching application controls and focus.
The current Info alert matches the original active blue OK button and background.
The failed child-process stage remains historical evidence and does not establish current parity.

The raw source-bound AX and images are in `evidence/jxa-exec-replay/`.
`../verification/fresh-proof.json` preserves their hashes and visual verdicts.
The capture tool supplies JPEG bytes under `.png` filenames; the verifier preserves those raw bytes.
No application visual mismatch is accepted through an aesthetic or layout improvement.
Full-product UX parity remains unestablished outside the five recorded workflows.
