# Repository rules

- Every author uses Simplified Technical English.
- Every author uses short sentences and active voice.
- Every author preserves quoted text and identifiers exactly.
- Every change keeps the implementation concise.
- A fix or refactor adds no more code than it removes.
- A new abstraction requires a concrete task need.
- The skill bundle follows the Agent Skills format.
- The main skill coordinates focused sibling skills.
- The skills use host-native invocation and task tools.
- The target project contains `recovered/`, `implementation/`, and `verification/`.
- The agent keeps temporary design and task plans outside the target project.
- The recovered test specifications record their origin and expected behavior.
- An evaluation freezes source and recovered models before original-source review.
- Every source-assisted repair remains explicit in its report.
- The repository keeps commit signing disabled locally.

The author runs `make test` after helper changes.
The author runs the affected evaluation after evaluation or implementation changes.
The author runs `make diagram` after architecture changes.
The author inspects each rendered diagram before delivery.
