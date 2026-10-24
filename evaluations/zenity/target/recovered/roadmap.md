# Native-dialog parity backlog

The original creator's future plans remain unknown.
The current implementation targets only the five contracted GUI workflows.
Full zenity product parity remains unestablished.

| Gap | Required original parity | Current state | Closure check |
| --- | --- | --- | --- |
| `JXA-ENTRY` | Entry acceptance and cancellation preserve native title, icon, controls, focus, text, and process results. | The source-assisted JXA code builds. Fresh GUI proof is missing. | Both fresh entry workflows must pass against the pinned reference. |
| `JXA-QUESTION` | Question Yes and No preserve the original native alert family and process results. | The source boundary now matches. Fresh GUI proof is missing. | Both fresh Question workflows must pass. |
| `JXA-INFO` | Info OK preserves the original native alert family and process results. | The source boundary now matches. Fresh GUI proof is missing. | The fresh Info workflow must pass. |
| `ZENITY-FULL` | Other original dialog modes, options, and platforms have one-to-one mappings and tests. | The smoke does not establish these mappings. | A separate explicit contract and complete original evidence must support any wider claim. |

All four gaps remain open.
The Mac is locked, so no fresh GUI case has completed.
Historical recordings cannot close current-source gaps.
The source-assisted code pin remains separate from the historical freeze.
