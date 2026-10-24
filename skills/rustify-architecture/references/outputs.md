# Architecture output schema

The canonical document is `recovered/architecture.md`.
The agent starts from [the document template](../assets/architecture.md).
The agent stores editable diagrams and supporting schemas under `recovered/evidence/architecture/`.
The state helper hashes that evidence directory.

## Required records

| Record | Fields |
| --- | --- |
| Component | `id`, name, responsibility, boundary, interfaces, state owner, execution model, evidence, classification, confidence, unknowns |
| Interface | `id`, caller, receiver, request and response form, ordering, errors, side effects, evidence |
| Edge | `id`, source component, target component, relation, control or data direction, evidence, classification, confidence, unknowns |
| Workflow | Scenario ID, trigger, numbered steps, component and edge IDs, failure paths, outcome, acceptance test IDs |
| State transition | State ID, event, guard, next state, effects, evidence, scenario IDs |
| Stored entity | Entity ID, fields, types, keys, relationships, constraints, evidence |
| Transaction | Transaction ID, participants, begin and commit boundaries, isolation, rollback, recovery, invariants, evidence |
| File format | Format ID, version, encoding, byte order, field ranges, lengths, checksums, invariants, unknown bytes, evidence |

The component and edge records use `observed`, `inferred`, or `unknown` classification.
Confidence has a level and a short reason.
Each diagram edge uses the same edge ID as its record.
A diagram cannot promote an inferred relationship to an observed fact.

## Diagram contract

The agent uses [the TikZ template](../assets/components-and-flows.tex) as an editable starting point.
The agent replaces its labels and Evidence IDs with recovered records.
The template shows a component view and a combined control/data-flow view.
The agent splits dense workflows into separate figures.
The agent draws a state machine only when observed state transitions require it.
An entity relationship diagram (ERD) represents observed stored entities.
The agent adds an ERD only when actual stored entities and relationships exist.
The agent supplies the corresponding schema and transaction or format records.
The schema artifact preserves observed declarations, engine version, field order, defaults, indexes, collation, and triggers.
The agent links schema migrations and compatibility rules to evidence.

The component view shows ownership boundaries and named interfaces.
Control edges carry ordered action labels.
Data edges carry payload and transformation labels.
The legend distinguishes control, data, and static relationships.
Each edge label or adjacent table identifies evidence and confidence.
The agent does not infer foreign keys or transaction atomicity from an ERD.

The agent renders the source to PDF and SVG when the toolchain supports them.
The agent inspects the render for clipping, overlapping labels, false joins, and unclear direction.
The agent documents one reproducible build command beside the diagram links.
For TikZ, the agent can use `latexmk -pdf -no-shell-escape -interaction=nonstopmode -halt-on-error components-and-flows.tex`.
The agent exports the component SVG with `pdftocairo -svg -f 1 -l 1 components-and-flows.pdf components.svg`.
The agent exports the workflow SVG with `pdftocairo -svg -f 2 -l 2 components-and-flows.pdf workflow.svg`.
The agent reports any unavailable renderer without replacing evidence with an invented diagram.

## Template substitution

The Markdown template uses `{{name}}` tokens.
The agent replaces every token with recovered content before publication.
The agent repeats table rows for actual components, edges, workflows, and data records.
The agent removes conditional storage and state sections when they do not apply.
The document then states the evidence search boundary for that absence.
The agent changes the TikZ label macros and the graph together.
The agent removes sample nodes and edges that lack target evidence.
The agent does not publish template examples as recovered facts.
