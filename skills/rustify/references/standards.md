# Standards and terminology

Every Rustify skill applies this guide to every artifact.
The guide names one standard for each concern.
The agent follows the standard and does not invent a local variant.

## Standards

| Concern | Standard | Rustify use |
| --- | --- | --- |
| Writing | [ASD-STE100 Simplified Technical English, Issue 9 (2025)](https://www.asd-ste100.org/) | Prose in every document, report, and comment. |
| Terminology | [ISO/IEC/IEEE 24765:2017](https://www.iso.org/standard/71952.html) systems and software engineering vocabulary; ISO 1087:2019 terminology principles | One term for each concept. |
| Verbal forms | [ISO/IEC Directives, Part 2](https://www.iso.org/sites/directives/current/part2/index.xhtml), clause 7 | "shall" for a requirement, "should" for a recommendation, "may" for a permission, and "can" for a possibility. |
| Requirements | [ISO/IEC/IEEE 29148:2018](https://www.iso.org/standard/72089.html); EARS (Mavin et al., RE 2009) | Requirement statements, attributes, and quality characteristics. |
| Architecture | [ISO/IEC/IEEE 42010:2022](https://www.iso.org/standard/74393.html); [C4 model](https://c4model.com); [arc42](https://arc42.org) | Concerns, viewpoints, views, correspondences, and document sections. |
| Decisions | [Nygard ADR](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions); [MADR](https://adr.github.io/madr/) | One immutable record for each design decision. |
| Verification and validation | [IEEE 1012-2024](https://standards.ieee.org/ieee/1012/7324/) | Verification methods, integrity, and independence. |
| Testing | ISO/IEC/IEEE 29119-1:2022 and 29119-3:2021 | Test basis, test oracle, test case, and test completion report. |
| Product quality | [ISO/IEC 25010:2023](https://www.iso.org/standard/78176.html) | Names of quality characteristics. |
| Assurance | ISO/IEC/IEEE 15026-2:2022; [GSN Community Standard v3](https://scsc.uk/gsn) | The structure of the compatibility report. |
| Life cycle | ISO/IEC/IEEE 12207:2017 | Names of processes: verification, validation, configuration management, and risk management. |

## Writing rules

These rules summarize ASD-STE100.
The agent obtains the complete standard from the ASD STEMG site when a rule is unclear.

- Use approved words with their approved meaning and part of speech.
- Use a technical name only for a concept in the glossary or in the target evidence.
- Use one word for one concept. Do not use synonyms.
- Do not use a noun cluster of more than three words.
- Write a procedural sentence with a maximum of 20 words.
- Write a descriptive sentence with a maximum of 25 words.
- Write one instruction in each sentence.
- Use the imperative for an instruction.
- Use the active voice and an explicit subject.
- Use the simple present, simple past, or simple future tense.
- Write a maximum of six sentences in a paragraph. Write one topic in each paragraph.
- Copy quoted text, command output, diagnostics, and identifiers exactly. These copies are exempt from the rules.

## Requirement rules

Each requirement describes one observed behavior of the original.
The Rust implementation must reproduce that behavior.

### Statement patterns

Each statement uses exactly one EARS pattern and exactly one "shall".

| Pattern | Form |
| --- | --- |
| `ubiquitous` | The `<system>` shall `<response>`. |
| `event` | When `<trigger>`, the `<system>` shall `<response>`. |
| `state` | While `<state>`, the `<system>` shall `<response>`. |
| `unwanted` | If `<condition>`, then the `<system>` shall `<response>`. |
| `optional` | Where `<feature>`, the `<system>` shall `<response>`. |
| `complex` | A combination of the `While`, `When`, `If`, and `Where` clauses, in that order. |

The `<system>` is the original product name from the contract.
The `<response>` states an observable result: bytes, status, state, effect, or interface change.
The statement does not name a Rust type, a library, or an inferred intent.

### Quality characteristics

ISO/IEC/IEEE 29148 defines these characteristics for each requirement.

- **Necessary**: The original exhibits the behavior.
- **Unambiguous**: The statement has one interpretation.
- **Complete**: The statement includes its trigger, conditions, and response.
- **Singular**: The statement contains one requirement.
- **Feasible**: A test, an inspection, an analysis, or a demonstration can verify it.
- **Verifiable**: The record names its verification method and its evidence.
- **Correct**: Original evidence supports the statement.

The requirement set must also be complete, consistent, and free of duplicates.

### Attributes

Each requirement record in `recovered/model.json` has these attributes.

| Attribute | Content |
| --- | --- |
| `id` | A stable identifier, for example `REQ-001`. |
| `dimension` | `product`, `ux`, `data`, or `behavior`. |
| `pattern` | One EARS pattern from the table above. |
| `statement` | The EARS statement. |
| `classification` | `observed`, `inferred`, or `unknown`. |
| `evidence` | Evidence identifiers for the original behavior. |
| `verification` | `test`, `inspection`, `analysis`, or `demonstration`. |
| `tests` | Declarative test identifiers for the `test` method. |
| `records` | Evidence identifiers for the other methods. |
| `components` | Original component identifiers that realize the requirement. |
| `in_scope` | `false` only for a requirement outside an authorized subset. |

## Architecture rules

The architecture description follows ISO/IEC/IEEE 42010.

- A **concern** is an interest of a stakeholder in the system.
- A **viewpoint** sets the conventions for one kind of view.
- A **view** shows the system from one viewpoint.
- A **correspondence** relates elements in two views or two descriptions.

Rustify uses these viewpoints.

| Viewpoint | Concern | Notation |
| --- | --- | --- |
| Context | Which users and external systems interact with the original? | C4 system context |
| Containers | Which processes, executables, libraries, and stores does the original use? | C4 container |
| Components | Which responsibilities and interfaces exist inside each container? | C4 component |
| Runtime | Which ordered calls and data transfers realize each workflow? | arc42 runtime view |
| State and data | Which states, stored entities, and formats does the original use? | State machine and ERD |

Each component record has `id`, `name`, `level`, `responsibility`, `classification`, and `evidence`.
The `level` is `container` or `component`.
Each edge record has `id`, `source`, `target`, `kind`, `classification`, and `evidence`.
The `kind` is `control`, `data`, or `static`.
A `control` or `static` edge points from the user to the used component.
The original-to-Rust mapping is a 42010 correspondence.
Each correspondence record has `original` and `rust`.
The `rust` value is one Rust source file that forms one module.

## Glossary

The agent uses these terms with these meanings.
The source column names the standard that defines the concept.

| Term | Meaning | Source |
| --- | --- | --- |
| original | The shipped software under reconstruction. Reports use the identifier `reference` for it. | Rustify |
| Rust implementation | The reconstruction in `implementation/`. Reports use the identifier `candidate` for it. | Rustify |
| requirement | A statement of a need and its constraints and conditions. | 29148 |
| evidence | Objective data that supports a claim. | 24765, 15026 |
| classification | `observed`, `inferred`, or `unknown` for a claim. | Rustify |
| test basis | The information that a tester uses to design tests. Here, the recovered model. | 29119-1 |
| test oracle | A source that determines expected results. Here, the original. | 29119-1 |
| characterization test | A test that records the actual behavior of existing software. | Feathers, *Working Effectively with Legacy Code* |
| verification | Confirmation with objective evidence that specified requirements are fulfilled. | 24765, IEEE 1012 |
| validation | Confirmation with objective evidence that the product fulfills its intended use. | 24765, IEEE 1012 |
| failure | An observed difference between the original and the Rust implementation. | 24765 |
| defect | The cause of a failure in the Rust implementation. | 24765 |
| gap | A known failure, an unknown result, or a missing mapping that stays open. | Rustify |
| exception | A user authorization to accept a stated difference. ISO/IEC/IEEE 24765 calls this a waiver. | 24765 |
| traceability | A relation between two work products, for example requirement and test. | 24765 |
| baseline | A frozen set of artifacts with recorded hashes. | 24765 |
| slice | A delivery increment that completes one or more requirements through all components. | Patton, *User Story Mapping* |
| walking skeleton | The first slice. It runs one real scenario end to end. | Cockburn; Freeman and Pryce |
| reflexion check | A comparison of the recovered component graph with the Rust module graph. | Murphy, Notkin, and Sullivan, FSE 1995 |
| convergence, divergence, absence | An edge in both graphs, only in the Rust graph, or only in the recovered graph. | Murphy, Notkin, and Sullivan |
| assurance case | A structured argument that evidence supports a claim. | 15026-2, GSN |
