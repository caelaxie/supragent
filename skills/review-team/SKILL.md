---
name: review-team
description: Launch a six-role parallel agent team to perform comprehensive code review of attached changes, pull requests, or codebase sections. Use for deep multi-role analysis that requires high-precision, evidence-backed findings, severity ranking, global issue numbering, concrete fixes, and patch-style diffs.
---

# Review Team

## Goal

Run six specialist reviewers in parallel and return one evidence-backed, deduplicated report.

## Inputs

- Review target (patch, PR diff, staged/uncommitted changes, or module).
- Stack/runtime context and constraints.
- Risk profile (auth, compliance, data integrity, availability).
- Scope exclusions.

## Workflow

### 1. Scope and ambiguity rules

Default mode: `changed-files-first`.
1. Review changed files.
2. Expand to immediate dependencies.
3. Expand to high-risk call paths only when evidence requires it.

If scope is ambiguous, proceed with explicit assumptions only for non-safety-critical paths.
If ambiguity affects security/auth/compliance/destructive operations/data integrity, stop and request clarification.

### 2. Build shared context packet

Include:
- Scope mode and assumptions.
- Change universe (`working-tree` or `commit-range`, plus exact range if known).
- Changed files + relevant tests/config.
- Commit allowlist/out-of-scope list (for downstream commit workflows).
- Severity/evidence policy.

### 3. Launch six roles in parallel

1. `Lead Architect`
   - Check layering boundaries, coupling hotspots, and abstraction leakage.
2. `Security Expert`
   - Check authn/authz, input validation, secrets handling, and reachable OWASP-class risks.
3. `Performance & Optimization Engineer`
   - Check hot-path complexity, redundant I/O, and memory churn.
4. `Readability & Maintainability Guru`
   - Check naming clarity, modularity/cohesion, and maintenance burden.
5. `Edge-Case & Testing Specialist`
   - Check null/empty paths, partial failures, races, and scale edge cases.
6. `Pragmatism & Simplicity Reviewer`
   - Check over-abstraction/indirection and propose behavior-preserving simplifications.

Guardrails:
- No speculative high-severity claims.
- Findings must cite concrete evidence.
- Anti-slop findings must provide behavior-preserving simplification.

### 4. Per-agent output schema

For each finding include:
- Severity (`Critical|High|Medium|Low`)
- Confidence (`High|Medium|Low`)
- Verification (`Confirmed|Likely|Hypothesis`)
- Title, Evidence, Impact, Suggested fix
- Diff (when feasible)
- Validation evidence (or explicit unverified disclosure)
- Behavior preservation note (required for anti-slop)
- Dependency policy note (required when the fix adds/changes external dependencies; cite approval or pre-approved policy)
- Regression test addition (required for Critical/High)

If no findings: explicit no-findings statement + residual risks.

Severity gates:
- `Critical/High` require strong evidence + `Confidence: High`.
- `Hypothesis` cannot exceed `Medium`.
- Anti-slop defaults to `Low/Medium`.
- Anti-slop cannot be `Critical` by itself.

### 5. Agent failure handling

- Wait for all six role outputs (or retry outcomes) before consensus synthesis.
- Retry failed role once.
- If a safety-critical role remains unavailable for in-scope risk, stop and request clarification before high-confidence conclusions.
- Otherwise continue with role marked `Unavailable` and apply confidence penalty.

### 6. Consensus

- Deduplicate by root cause/component/risk type.
- Merge overlaps and list contributing roles.
- Escalate severity by at most one level with corroboration.
- Remove style-only nits unless impact is material.
- Keep disagreements under `Open Questions`.

## Final Output Contract

Return one consolidated report with sections:
1. `Executive Summary`
2. `Scope Reviewed` (must include change universe)
3. `Coverage Limits`
4. `Role Coverage` (for each of 6 roles: `Completed|No findings|Unavailable`)
5. `Findings (Critical -> High -> Medium -> Low)` with global `Issue N` numbering
6. `Quick Wins`
7. `Suggested Diffs`
8. `Regression Test Additions`
9. `Open Questions`
10. `Residual Risks`

Quality gates:
- Every finding has evidence, impact, fix, and validation evidence/unverified disclosure.
- Critical/High satisfy strict evidence rules.
- Anti-slop findings include behavior-preservation note.
- Numbering is gap-free and uncapped.

## Compatibility

- Generator skills (for example `d2lang`) own final user-facing output; `review-team` output becomes internal analysis input.
- With `commit` (and no generator), append `Commit Scope` after `Residual Risks` and keep staging allowlisted.
- With generator + `commit`, pass `Commit Scope` as internal handoff data (not appended section).
- `pr` and `review-team` must run as separate flows. Do not co-trigger or merge output contracts in one response.
