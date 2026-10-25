# Interaction investigation methods

## Establish repeatable captures

The agent records the original version, platform, locale, theme, scale, viewport, and input method when applicable.
The agent records the document, session, and persisted settings that establish each initial state.
The agent captures the original before it designs the Rust interface.
The agent uses separate experiment data and coordinates shared application state with the orchestrator.

The agent inventories screens, routes, dialogs, panels, menus, and entry points.
Each interface state receives a stable identifier.
The inventory includes empty, populated, selected, loading, disabled, error, interrupted, and recovery states when the original exposes them.
The agent follows navigation forward and back through complete workflows.
An unvisited route or unobserved state remains a coverage gap.

## Recover visual and interaction contracts

| Surface | Original evidence to capture |
| --- | --- |
| Layout | The agent captures hierarchy, dimensions, spacing, alignment, resizing, scrolling, clipping, and window constraints. |
| Components | The agent captures labels, values, enabled conditions, selection, hover, press, focus, validation, and error states. |
| Tokens | The agent records observed color values, fonts, sizes, weights, line heights, borders, radii, shadows, and spacing units. |
| Assets | The agent records resource identity, dimensions, variants, rendering mode, and where the original uses each asset. |
| Keyboard and focus | The agent captures tab order, initial focus, shortcuts, default actions, escape behavior, focus return, and visible focus indicators. |
| Pointer and drag | The agent captures hit targets, gestures, drag thresholds, accepted drops, feedback, cancellation, and final state. |
| State and motion | The agent captures transition triggers, loading feedback, animation timing when observable, interruption, cancellation, and recovery. |
| Data and persistence | The agent captures edits, validation timing, save behavior, unsaved changes, restart state, and destructive-action feedback. |

The agent measures values from captures or resources and records the measurement method.
The agent does not replace an unknown value with a preferred design token.
The agent records accessibility behavior only when the original exposes supporting evidence.

## Recover nonvisual interfaces

For a CLI, the agent captures exact syntax, option grouping, defaults, operands, input sources, stdout, stderr, status, and formatting.
The agent captures help and version output and preserves byte-level diagnostics.
The agent tests terminal-dependent behavior only under recorded terminal conditions.
For a service, the agent captures request, response, sequencing, cancellation, and observable state.
For a game, the agent captures controls, modes, feedback, saves, and the original motion or frame behavior.
The agent marks visual tokens inapplicable only when the interface has no visual surface.

## Use REA and preserve provenance

The agent discovers actual REA tool schemas and uses the existing provider.
The agent uses supported UI, resource, string, handler, and execution evidence to resolve specific interaction questions.
The agent preserves REA Evidence IDs and original capture paths.
The agent exports needed evidence before session closure and coordinates session ownership with the orchestrator.
A provider limitation remains explicit; it does not justify an invented interaction.
Static resource evidence does not prove that a screen displays that resource.
The agent confirms usage through a runtime capture when possible.

## Turn captures into requirements

Each state and transition becomes one or more `ux` requirements in EARS form.
For example: "When the user presses Escape in the entry dialog, the zenity program shall exit with status 1."
Each requirement links to an original capture, a scenario, and a declarative expectation.
A proposed replay can add a new action sequence. The original must supply its outcome before it becomes a requirement.
An inferred transition stays `inferred` until a probe establishes the result.
The agent does not close a gap through a redesign, normalization, or preferred behavior.
The agent writes only its assigned shards. The orchestrator merges them.
