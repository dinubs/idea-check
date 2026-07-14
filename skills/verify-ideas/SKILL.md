---
name: verify-ideas
description: Verify whether plain-language product idea Markdown files remain true in the current implementation and environment. Use for idea checks, continuous idea verification, pre-merge or release validation, scheduled product audits, falsification passes, and evidence-backed checks of claims under ideas/ or another configured ideas directory.
---

# Verify Ideas

Treat the idea files as human-owned claims and the implementation as evidence. Attempt to falsify each selected idea against the current product. Do not convert ideas into a requirements DSL and do not treat existing tests as the definition of truth.

## Run a verification

1. Locate the Idea Check runner. Prefer `bin/idea-check` in the project, then `idea-check` on `PATH`, then this skill's `scripts/idea_check.py`.
2. Run `prepare` to create a request, prompt, and report schema under `.idea-check/current/`. Pass an optional free-form `--context` or repeat `--idea <id>` to narrow the run when the user asks.
3. Read `references/verification-protocol.md` and the generated request before investigating.
4. Inspect the available code, tests, runtime, browser, deployment artifact, or operational evidence as the environment permits.
5. Try realistic failure paths and boundary conditions. Use existing tests as evidence, or create disposable probes only under `.idea-check/current/work/`.
6. Do not edit tracked product files, idea files, tests, or configuration during verification.
7. Return one report conforming to `.idea-check/current/report-schema.json` and save it as `.idea-check/current/report.json` when filesystem writes are available.
8. Run `validate` against the request and report. Report its deterministic exit result without overriding it.

## Preserve epistemic honesty

- Mark an idea `supported` only when direct evidence covers its material claim and stated falsification conditions.
- Mark it `contradicted` when direct evidence shows the claim is false.
- Mark it `inconclusive` when important evidence is missing, ambiguous, or only inferred.
- Mark it `blocked` when the environment prevents a meaningful check.
- Distinguish direct observations from inference in every evidence entry.
- Never interpret ambiguity in the convenient direction. Record it as a gap.
- Never claim production behavior from source inspection or local tests alone.

## Adapt to the environment

Inventory available tools before planning the check. Use the strongest evidence available without assuming a particular language, framework, browser, provider, or CI system. If a required capability is unavailable, preserve the gap instead of fabricating a substitute.

Read `references/report-format.md` when producing or diagnosing reports. Copy `assets/example-idea.md` only when the user asks to create an idea file.
