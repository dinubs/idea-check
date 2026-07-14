# Verification protocol

## Authority

The selected idea files are normative and human-owned. Code, tests, documentation, and prior reports are non-normative evidence. Do not revise an idea to match the implementation.

## Investigation

For every selected idea:

1. Restate the material claim privately before choosing checks.
2. Identify concrete conditions that would make it false.
3. Inspect recent changes and relevant implementation paths.
4. Prefer direct behavioral evidence over source inspection.
5. Exercise boundaries, failure paths, and cross-component behavior.
6. Use prior reports only to find regression risks; re-establish current evidence.
7. Record commands, exit codes, locations, and artifacts precisely enough to reproduce the observation.

Use existing tests when they probe the idea. A green suite alone is not sufficient unless the suite directly covers the complete claim. Disposable probes belong under the run's `work/` directory and must not remain in the project.

## Result meanings

- `supported`: Direct current evidence supports every material part of the idea in the environment being claimed.
- `contradicted`: Direct current evidence demonstrates at least one material part is false.
- `inconclusive`: The investigation ran, but evidence is incomplete, ambiguous, stale, or too indirect.
- `blocked`: A missing service, credential, tool, environment, or other external condition prevented meaningful investigation.
- `not_applicable`: The request explicitly selected an idea that cannot apply to the stated context or artifact. Explain why; use sparingly.

## Integrity rules

- Do not edit tracked files.
- Do not weaken checks or reinterpret ideas to obtain a pass.
- Do not report a command as passing unless it was executed in this run.
- Do not infer production truth from local behavior.
- Do not omit selected ideas. The deterministic validator rejects omissions and duplicates.
- Keep secrets and sensitive output out of evidence.

## Run context

Treat the request's optional context as open-ended guidance about why verification is happening now. It may describe a change, incident, environment, artifact, risk, or review cadence. Do not reinterpret it as a fixed mode, and do not persist it back into idea files.

When no context is supplied, perform the strongest general verification available. When specific ideas are selected, investigate only those ideas while preserving their complete meaning.
