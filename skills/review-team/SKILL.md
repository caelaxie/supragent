---
name: review-team
description: Launch a six-role parallel agent team to perform comprehensive code review of attached changes, pull requests, or codebase sections. Use for deep multi-role analysis that requires high-precision, evidence-backed findings, severity ranking, global issue numbering, concrete fixes, and patch-style diffs.
---

# Review Team

## Overview

Run six specialist reviewers in parallel, then synthesize one high-precision consensus report.

Default behavior:
- Prioritize precision over recall.
- Avoid speculative high-severity claims.
- Produce comprehensive deep-dive output.
- Report uncapped findings with global numbering (`Issue 1`, `Issue 2`, ...).

## Inputs to collect

- Review target: attached patch, PR diff, staged/uncommitted changes, or codebase section.
- Stack context: language/runtime/frameworks and major architecture constraints.
- Risk profile: auth, payments, data integrity, availability, compliance-sensitive paths.
- Scope constraints: directories/files excluded from review, if any.

## Workflow

### 1. Establish scope mode and depth budget

Use `changed-files-first` as the default mode:
1. Review changed files first.
2. Expand to immediate dependencies referenced by changed code.
3. Expand to high-risk call paths only when evidence requires it.

Alternative modes (only when explicitly requested):
- `risk-hotspot`: prioritize auth/data/external-I/O boundaries.
- `targeted-module`: focus on user-specified modules only.

If scope is ambiguous, state assumptions and continue with best-effort review.
Always record untouched but relevant areas under `Coverage Limits`.

### 2. Build context packet for all reviewers

Pass the same base context to every reviewer:
- Scope summary and selected mode.
- Changed files and relevant configuration/test artifacts.
- Known assumptions and constraints.
- Severity and evidence policy from this skill.

### 3. Launch specialist agents in parallel

Create one subagent per role and run all six concurrently.

Role prompts:

1. `Lead Architect`
   - Must check layering boundaries, coupling hotspots, abstraction leakage, and scalability limits.
   - Guardrail: do not flag architectural drift without concrete dependency/path evidence.
2. `Security Expert`
   - Must check OWASP classes, authz/authn paths, input validation, secrets handling, and supply-chain risk.
   - Guardrail: do not claim vulnerabilities without reachable code-path evidence.
3. `Performance & Optimization Engineer`
   - Must check algorithmic complexity, hot-path waste, redundant I/O, memory churn, and unused code.
   - Guardrail: do not claim bottlenecks without plausible runtime path and code evidence.
4. `Readability & Maintainability Guru`
   - Must check naming clarity, modularity, cohesion, testability, and maintenance burden.
   - Guardrail: avoid style-only nits unless they materially affect correctness or maintainability.
5. `Edge-Case & Testing Specialist`
   - Must check null/empty paths, race conditions, partial failures, i18n/timezone issues, and 10x scale behavior.
   - Guardrail: tie every edge-case claim to a specific branch/condition.
6. `Junior-Developer Simulator`
   - Must check confusing APIs, misuse-prone abstractions, brittle extension points, and likely onboarding mistakes.
   - Guardrail: keep findings concrete and evidence-backed.

Provide each subagent with:
- Context: scope summary and diff/files under review.
- Dependencies: assumptions and known completed work.
- Related tasks: adjacent files, systems, or reviewers that influence analysis.
- Exact task: role-specific checks and expected finding format.
- Validation: tests or checks to reference for confidence.
- Constraints: avoid speculation without evidence; cite concrete evidence.

### 4. Enforce per-agent output schema

Require every subagent response to use this structure:

1. `Findings` (zero or more)
   - `Severity`: Critical | High | Medium | Low
   - `Confidence`: High | Medium | Low
   - `Verification`: Confirmed | Likely | Hypothesis
   - `Title`: concise issue name
   - `Evidence`: file/line references or precise artifact references
   - `Impact`: why this matters
   - `Suggested fix`: concrete remediation steps
   - `Diff`: patch-style suggestion when feasible (required for every finding when feasible)
   - `Regression test addition`: required for Critical/High; optional for Medium/Low
2. `No findings` statement when the agent finds no actionable issues.
3. `Residual risks` for concerns that are plausible but unproven.

Severity gate policy:
- Report `Critical` or `High` only with strong concrete evidence and `Confidence: High`.
- Downgrade uncertain high-severity concerns.
- `Hypothesis` findings cannot exceed `Medium`.

### 5. Handle agent failures without blocking

Wait for all six subagents to finish before synthesizing.
If any subagent fails or times out:
1. Retry that role once.
2. If retry fails, continue and mark role `Unavailable`.
3. Add a confidence penalty note in the final report.

### 6. Build deterministic consensus

Consensus rules:
1. Deduplicate by `(root cause, component, risk type)`.
2. Merge overlapping findings into one issue with multiple roles listed.
3. Escalate severity by at most one level when multiple roles corroborate.
4. Preserve unresolved disagreements in `Open Questions`.
5. Remove style-only nits unless they materially impact correctness, security, performance, or maintainability.

Severity rubric:
- `Critical`: exploitable vulnerability, data loss/corruption risk, auth bypass, or outage-class defect.
- `High`: significant correctness/security/performance risk likely to affect production behavior.
- `Medium`: meaningful maintainability/reliability/testability issue with moderate impact.
- `Low`: minor issue with limited impact, polish-level improvement, or low-risk cleanup.

### 7. Apply quality gates before final output

Before finalizing, verify:
1. Findings are globally numbered without gaps as `Issue N`.
2. Every finding includes evidence, impact, and concrete fix.
3. Critical/High findings satisfy strict evidence gate.
4. Duplicate root-cause findings are merged.
5. `Open Questions` exists as a dedicated section.
6. Findings list is uncapped.
7. Regression test additions are included for every Critical/High finding.

### 8. Produce final output

Return exactly one consolidated report using this shape:

````markdown
## Executive Summary
- <top risks, overall confidence, affected areas>

## Scope Reviewed
- <what was reviewed>
- <assumptions and constraints>

## Coverage Limits
- <what was intentionally out-of-scope or not fully inspected>
- <missing context that reduced confidence>

## Findings (Critical → High → Medium → Low)
Continue numbering without a cap (`Issue N`).
### Critical
1. Issue 1: <title>
- Roles: <which agents flagged it>
- Confidence: <High|Medium|Low>
- Verification: <Confirmed|Likely|Hypothesis>
- Evidence: <file:line or artifact>
- Impact: <why it matters>
- Fix: <concrete change>
- Regression Test Addition: <required for Critical/High>
2. Issue 2: <title>
...

### High
N. Issue N: <title>
...

### Medium
N. Issue N: <title>
...

### Low
N. Issue N: <title>
...

## Quick Wins
- <high-impact, low-effort changes>

## Suggested Diffs
### Issue 1
```diff
<diff for Issue 1; if infeasible, say why>
```

### Issue 2
```diff
<diff for Issue 2; if infeasible, say why>
```
### Issue N
```diff
<diff for each additional issue; if infeasible, say why>
```

## Regression Test Additions
- Include entries for every Critical/High issue only.
- Issue N: <required test addition for each Critical/High issue>
- If no Critical/High findings exist, write: `None`.

## Open Questions
- <uncertainties, tradeoffs, or evidence gaps that need follow-up>

## Residual Risks
- <free-form remaining risk after proposed fixes>
````

If no findings exist, state:
- `No issues found at Critical/High/Medium/Low.`
- Residual risks and testing gaps that still warrant follow-up.

## Quality bar

1. Prioritize actionable findings over broad commentary.
2. Cite evidence for every nontrivial claim.
3. Prefer small, concrete fix suggestions.
4. Include patch-style diffs for every finding when feasible.
5. Number every discovered issue with `Issue N`.
6. Keep output comprehensive and decision-useful.

## Validation scenarios

Use these checks to self-validate output quality:

1. Corroborated critical issue:
   - Input has a real auth bypass path confirmed by multiple roles.
   - Expected: single merged Critical issue with high confidence, diff, and regression test addition.
2. Speculative security concern:
   - Input suggests potential injection without full data-flow proof.
   - Expected: downgraded to Medium with `Verification: Hypothesis` and explicit follow-up question.
3. Duplicate finding across roles:
   - Perf and maintainability roles flag same root cause.
   - Expected: one merged issue listing both roles.
4. Partial agent failure:
   - One role times out and retry fails.
   - Expected: final report completes, marks role unavailable, and applies confidence penalty note.
5. Clean patch:
   - Input has no actionable defects.
   - Expected: explicit no-findings statement plus free-form residual risks.
