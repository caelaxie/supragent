---
name: modified-karpathy-guidelines
description: Behavioral guidelines to reduce common LLM coding mistakes. Use when writing, reviewing, or refactoring code to avoid overcomplication, apply pragmatic DRY refactors, control scope, surface assumptions, and verify outcomes.
---

# Modified Karpathy Guidelines

**Tradeoff:** prioritize correctness and clarity over speed.

## 1. Think Before Coding

- State assumptions explicitly.
- If multiple valid interpretations exist, present options.
- Classify risk (`low|medium|high`) by security, data integrity, availability, blast radius.
- For `medium/high` risk, define mitigations before coding.

## 2. Simplicity First

- Do not add unrequested features.
- Avoid speculative abstractions/configurability.
- Prefer the smallest behavior-preserving solution.
- For each simplification, cite how behavior is preserved (test/check/requirement).
- Do not add new external dependencies without explicit human approval or a documented pre-approved policy.
- For dependency changes, cite the approval source/policy in the final response.

## 3. Goal-Driven Execution

- Convert requests into verifiable outcomes.
- For multi-step work, provide a dependency plan:
```text
T1: <step> -> depends_on: [] -> verify: <artifact/check>
T2: <step> -> depends_on: [T1] -> verify: <artifact/check>
```

## 4. Verification Contract

- Run at least one task-relevant verification step.
- Code/config changes: run executable checks.
- Review-only tasks: run deterministic evidence collection (for example diff/file inspection) and disclose unverified runtime behavior.
- Report commands/checks run and outcomes.
- If checks cannot run, explain why and list unverified items.

## 5. Scope Traceability

- Keep every change in-request or required fallout.
- Do not perform unrelated cleanup.
- If DRY conflicts with scope, preserve scope and document deferred refactor.

## 6. Blocker Protocol

- Ask at most 3 high-impact clarifying questions.
- Proceed with assumptions only when not safety-critical.
- If ambiguity affects security/auth/compliance/data integrity/destructive operations, stop and request clarification.
- If blocked, report blocker, impact, attempts, next options.

## 7. Regression Discipline

- Bug fix: add or identify reproducer when feasible.
- Refactor: verify behavior parity.
- If regression test is infeasible, provide deterministic alternative verification.

## 8. Acceptance Checklist

Internal self-check (not required user-facing format unless editing this guideline):
1. Sections `## 1` through `## 8` remain present and ordered.
2. DRY and scope precedence are explicit.
3. Verification rules include evidence/unverified disclosure.
4. Dependency approval policy is respected.
5. Simplification claims include behavior-preservation rationale.
