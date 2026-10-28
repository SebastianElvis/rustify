# Architecture output rules

The canonical records are the `components` and `edges` sections of `recovered/model.yaml`.
The canonical document is `recovered/architecture.md`.
The agent starts from [the document template](../assets/architecture.md).
The agent stores editable diagrams and supporting schemas under `recovered/evidence/architecture/`.
The state helper hashes that evidence directory.

## Ledger records

| Record | Fields |
| --- | --- |
| Component | `id`, `name`, `level` (`container` or `component`), `responsibility`, `classification`, `evidence` |
| Edge | `id`, `source`, `target`, `kind` (`control`, `data`, or `static`) |

`recovered/architecture.md` states the classification and evidence of each edge.
A `control` or `static` edge points from the user to the used component.
A `data` edge points from the producer to the consumer.
The reflexion check compares `control` and `static` edges with Rust module dependencies.
The agent records a component only for an evidenced responsibility and boundary.
A source filename or compiler symbol alone does not establish a boundary.

## Document records

The document adds these records to the ledger items.

| Record | Fields |
| --- | --- |
| Interface | Caller, receiver, request and response form, ordering, errors, side effects, evidence |
| Runtime trace | Scenario ID, trigger, numbered steps, component and edge IDs, failure paths, outcome, requirement IDs |
| State transition | State ID, event, guard, next state, effects, evidence, scenario IDs |
| Stored entity | Entity ID, fields, types, keys, relationships, constraints, evidence |
| Transaction | Participants, begin and commit boundaries, isolation, rollback, recovery, invariants, evidence |
| File format | Version, encoding, byte order, field ranges, lengths, checksums, invariants, unknown bytes, evidence |

The document names every component ID in the ledger.
Confidence has a level and a short reason. Confidence does not replace the classification.
A diagram cannot promote an inferred relationship to an observed fact.

## Diagram contract

The agent uses [the TikZ template](../assets/components-and-flows.tex) as an editable starting point.
Each diagram node and edge uses the same identifier as its ledger record.
The agent splits dense workflows into separate figures.
The agent adds an ERD only when actual stored entities and relationships exist.
The agent does not infer foreign keys or transaction atomicity from an ERD.

The agent renders the source to PDF and SVG when the toolchain supports them.
The agent inspects the render for clipping, overlapping labels, false joins, and unclear direction.
For TikZ, the agent can use `latexmk -pdf -no-shell-escape -interaction=nonstopmode -halt-on-error components-and-flows.tex`.
The agent exports each page with `pdftocairo -svg -f N -l N components-and-flows.pdf view-N.svg`.
The agent reports any unavailable renderer without replacing evidence with an invented diagram.

## Template substitution

The agent replaces every `{{name}}` token with recovered content.
The agent repeats table rows for actual components, edges, traces, and data records.
The agent removes conditional storage and state sections when they do not apply and states the search boundary.
The agent removes sample diagram nodes and edges that lack target evidence.
