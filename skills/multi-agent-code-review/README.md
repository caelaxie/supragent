# Multi-Agent Code Review Skill

## Overview

A comprehensive code review system that deploys 6 specialized agents working in parallel to analyze code changes from different perspectives. Agents convene for a final consensus report with ranked findings and concrete fix suggestions.

## Team Roles

1. **Lead Architect** - Overall structure, scalability, design patterns
2. **Security Expert** - OWASP, injection, auth, secrets, supply-chain risks  
3. **Performance & Optimization Engineer** - Time/space complexity, bottlenecks, unused code
4. **Readability & Maintainability Guru** - Naming, comments, SOLID, testability
5. **Edge-Case & Testing Specialist** - Nulls, concurrency, internationalization, 10x scale
6. **Junior-Developer Simulator** - Spots things a junior would miss or introduce

## Usage

### With Codex

```bash
# In your project directory
codex review --skill /path/to/multi-agent-code-review

# Or with specific files
codex review --skill /path/to/multi-agent-code-review --files src/
```

### With Opencode

```bash
# In your project directory
opencode --skill /path/to/multi-agent-code-review

# Or with PR/diff
opencode --skill /path/to/multi-agent-code-review --diff changes.patch
```

### Manual Execution

```python
from skills.multi_agent_code_review.main import CodeReviewTeam

team = CodeReviewTeam()
report = team.review(code_diff="""...""", pr_description="...")
print(report.markdown())
```

## Output Format

The skill generates a markdown report with:
- **Executive Summary** - High-level overview
- **Findings by Severity** - Critical/High/Medium/Low
- **Per-Agent Analysis** - Detailed findings from each agent
- **Consensus Report** - Agreed-upon critical issues
- **Suggested Fixes** - Code diffs and patches

## Configuration

Edit `config.json` to customize:
- Severity thresholds
- Output format
- Agent timeout settings
- Consensus rules

## File Structure

```
multi-agent-code-review/
├── skill.json              # Skill metadata
├── config.json             # Configuration options
├── main.py                 # Orchestrator
├── consensus.py            # Consensus builder
├── prompts/                # Agent system prompts
│   ├── lead-architect.txt
│   ├── security-expert.txt
│   ├── performance-engineer.txt
│   ├── maintainability-guru.txt
│   ├── edge-case-specialist.txt
│   └── junior-dev-simulator.txt
└── README.md
```

## Ranking System

Findings are ranked by severity:
- **Critical** - Security vulnerabilities, data loss risks, crashes
- **High** - Performance issues, architectural flaws, major bugs
- **Medium** - Maintainability issues, edge cases, missing tests
- **Low** - Style issues, minor optimizations, suggestions

## Contributing

To add new agent roles or modify existing ones, edit the prompts in `prompts/` and update `skill.json`.
