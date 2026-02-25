---
name: review-team
description: Create and launch a multi-agent team to perform comprehensive code review of attached changes, pull requests, or specific codebase sections. Use when asked for deep code review, multi-role analysis, severity-ranked findings, security/performance/architecture critique, or a final consensus report with concrete fixes and code diffs.
---

# Review Team

## Overview

Create six specialist reviewers, run them in parallel, then merge results into one consensus report ranked by severity.

## Workflow

### 1. Define review scope

1. Identify the review target:
   - Attached patch or staged changes
   - Pull request diff
   - User-specified codebase section
2. Gather context needed for analysis:
   - Diff and changed files
   - Related implementation files
   - Relevant tests and configuration
3. If scope is ambiguous, state assumptions explicitly and continue with best-effort review.

### 2. Launch specialist agents in parallel

Create one subagent for each role and run all of them concurrently.

Role prompts:

1. `Lead Architect`
   - Evaluate architecture, boundaries, design patterns, coupling/cohesion, scalability risks, and long-term extensibility.
2. `Security Expert`
   - Evaluate OWASP risks, injection vectors, authz/authn flaws, secrets handling, dependency and supply-chain risks, and unsafe defaults.
3. `Performance & Optimization Engineer`
   - Evaluate algorithmic complexity, hot paths, memory/CPU bottlenecks, I/O overhead, redundant work, and dead or unused code.
4. `Readability & Maintainability Guru`
   - Evaluate naming clarity, code organization, comment quality, SOLID adherence, modularity, and ease of testing/refactoring.
5. `Edge-Case & Testing Specialist`
   - Evaluate null/empty handling, race/concurrency hazards, failure modes, i18n/locale behavior, and behavior under 10x scale.
6. `Junior-Developer Simulator`
   - Simulate mistakes a junior engineer may introduce or overlook; identify confusing patterns and likely misuse points.

Provide each subagent with:
- Context: scope summary and diff/files under review.
- Dependencies: known completed work and assumptions.
- Related tasks: adjacent files, systems, or reviewers that influence analysis.
- Exact task: role-specific checks and expected finding format.
- Validation: tests or checks to reference for confidence.
- Constraints: avoid speculation without evidence; cite concrete evidence.

### 3. Enforce per-agent output schema

Require every subagent response to use this structure:

1. `Findings` (zero or more)
   - `Severity`: Critical | High | Medium | Low
   - `Title`: concise issue name
   - `Evidence`: file/line references or precise artifact references
   - `Impact`: why this matters
   - `Suggested fix`: concrete remediation steps
   - `Diff` (optional): minimal patch-style suggestion when practical
2. `No findings` statement when the agent finds no actionable issues.
3. `Residual risks` for concerns that are plausible but unproven.

### 4. Build consensus report

Wait for all six subagents to finish before synthesizing.

Consensus rules:
1. Merge duplicates that share the same root cause.
2. Escalate severity when multiple roles corroborate the same issue.
3. Preserve minority concerns in `Open Questions` when evidence is incomplete.
4. Remove purely stylistic nits unless they materially impact correctness, security, performance, or maintainability.

Severity rubric:
- `Critical`: exploitable vulnerability, data loss/corruption risk, auth bypass, or outage-class defect.
- `High`: significant correctness/security/performance risk likely to affect production behavior.
- `Medium`: meaningful maintainability/reliability/testability issue with moderate impact.
- `Low`: minor issue with limited impact, polish-level improvement, or low-risk cleanup.

### 5. Produce final output

Return exactly one consolidated report using this shape:

````markdown
## Scope Reviewed
- <what was reviewed>
- <assumptions and constraints>

## Findings (Critical → High → Medium → Low)
Use one global counter for discovered issues across all severities (`Issue 1`, `Issue 2`, ...).

### Critical
1. Issue 1: <title>
- Roles: <which agents flagged it>
- Evidence: <file:line or artifact>
- Impact: <why it matters>
- Fix: <concrete change>
```diff
<optional diff>
```

### High
2. Issue 2: <title>
...

### Medium
3. Issue 3: <title>
...

### Low
4. Issue 4: <title>
...

## Open Questions
- <items requiring clarification>

## Residual Risks
- <remaining risk after proposed fixes>
````

If no findings exist, state:
- `No issues found at Critical/High/Medium/Low.`
- Residual risks and testing gaps that still warrant follow-up.

## Quality bar

1. Prioritize actionable findings over broad commentary.
2. Cite evidence for every nontrivial claim.
3. Prefer small, concrete fix suggestions.
4. Include patch-style diffs when they materially speed implementation.
5. Number every discovered issue in the final report with a clear issue index.
6. Keep output concise but decision-useful.
