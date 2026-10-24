# Recovered native-dialog specification

The scope contains five original Entry, Question, and Info workflows.
The original reference captures remain in `evidence/` and the historical archive.
Those captures specify original behavior but do not validate new candidate source.

| Interface | Original native family | Title and text | Controls |
| --- | --- | --- | --- |
| Entry | JXA `displayDialog` | `withTitle` carries the title. The dialog argument carries the message. `defaultAnswer` carries seed text. | OK and Cancel appear. The accepted text reaches stdout with a newline. |
| Question CLI defaults | JXA `displayAlert` | The alert argument carries the title. `message` carries the text. | Yes and No appear. No cancels with status 1. |
| Info | JXA `displayAlert` | The alert argument carries the title. `message` carries the text. | OK appears. Acceptance returns status 0 with empty output. |

The CLI supplies the Question labels, which selects the original alert path.
The original script uses currentApplication standard additions and native default appearance.
The source-assisted candidate now uses that same OS script boundary.
The old direct-AppKit icon and title-placement differences are not accepted as current parity.
Fresh replay must compare native family, title presentation, default icon, controls, focus, and process results.
No current visual parity result exists while the Mac remains locked.
Full-product UX parity remains unestablished.
