# Completion protocol

## Build the private completion checklist

Derive the checklist from the idea's actual language:

- The primary user or system outcome.
- Every named circumstance in which it must remain true.
- Explicit statements describing when the idea is false.
- Ownership, security, durability, failure, and recovery boundaries implied by the claim.
- User-visible states and language needed for the promise to be honest.
- Evidence needed to distinguish direct support from inference.

Keep this checklist as working reasoning or a temporary run artifact. The idea file remains the only normative statement.

## Cover the product, not only the code path

Consider each layer only when relevant:

- Persistent data and migration of existing state.
- Domain rules and cross-record invariants.
- Authorization and ownership boundaries.
- Service and background-job behavior.
- APIs, routes, user interfaces, and accessibility.
- Retries, concurrency, partial failure, and recovery.
- Deployment configuration and external integrations.
- Logs, metrics, alerts, and evidence required after deployment.
- Tests at the level where the claim can actually fail.

Do not create layers merely to satisfy the list. Use it to avoid declaring a cross-system idea complete after changing one local function.

## Resist specification gaming

- Do not narrow ordinary words into a convenient technical interpretation without user approval.
- Do not replace direct behavior with mocks when the idea concerns a real integration boundary.
- Do not change tests to accept broken behavior.
- Do not treat absence of a failing test as evidence of support.
- Do not mark unresolved evidence as future work and still claim completion.

## Verification loop

The implementation loop ends only on a supported Idea Check report. If verification finds a local gap, implement the missing behavior or evidence and verify again. If verification exposes ambiguity that changes product meaning, request the human decision instead of choosing silently.
