---
name: implement-idea
description: Implement one human-owned product idea Markdown file completely, iterating across code, tests, documentation, migrations, interfaces, and observability until fresh evidence supports the idea. Use when the user invokes implement-idea, asks to implement an idea from ideas/, wants an accepted product claim made fully true, or asks an agent to continue until an idea is fully embodied in the product.
---

# Implement Idea

Make one selected idea true in the product. Treat the idea file as human-owned intent, not as text to rewrite around the current implementation.

## Select and understand the idea

1. Use the exact path or ID supplied by the user. Otherwise run `bin/idea-check list` or the available Idea Check runner to discover ideas.
2. Ask one concise question only when multiple ideas remain plausible and choosing would materially change the work.
3. Read the complete idea, repository instructions, related ideas, and relevant implementation before editing.
4. Translate the idea into a private completion checklist covering every material claim, boundary, and stated falsification condition. Do not add this checklist to the idea file as a new specification language.
5. Identify what is already true, what is missing, and what evidence would establish completion.

Read `references/completion-protocol.md` before implementation.

## Implement to completion

1. Plan the smallest coherent change that can embody the whole idea.
2. Change every necessary layer: data model, migrations, services, interfaces, failure behavior, tests, documentation, and observability as applicable.
3. Follow repository-local instructions and preserve unrelated user changes.
4. Run focused checks while iterating, then broaden verification in proportion to the idea's scope and risk.
5. Compare the current product with every item in the private completion checklist after each meaningful pass.
6. Continue implementing when any material part remains false, unhandled, or supported only by assumption.

Do not stop because code compiles, a happy-path test passes, or a task list is checked off. “Fully in” means the complete product claim is embodied across its real boundaries.

## Verify the finished idea

After implementation changes are settled:

1. Run Idea Check `prepare --idea <id>` with free-form context describing the implementation just completed.
2. Perform the `verify-ideas` falsification protocol against the selected idea. Prefer a fresh agent or independent subagent when the harness supports it. Otherwise perform an explicit adversarial pass and disclose that the implementer also verified.
3. Save and validate the structured report.
4. If the result is `contradicted` or `inconclusive` because of an implementation or evidence gap that can be resolved locally, return to implementation and repeat.

## Finish honestly

Finish only when:

- Fresh evidence supports every material part of the selected idea.
- Relevant focused and broad checks pass.
- The implementation did not weaken or silently reinterpret the idea.
- The final response states what changed, what evidence supports it, and any residual limits outside the idea's claim.

Stop as blocked only when completion requires unavailable authority, credentials, external coordination, or a product decision that would change the idea. State the exact blocker and preserve all useful completed work. Never edit the idea merely to turn a blocked or contradicted result into support.
