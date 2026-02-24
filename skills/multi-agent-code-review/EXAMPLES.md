# Multi-Agent Code Review Usage Examples

## Quick Start

### With Codex

Add to your `.codex` file or project configuration:

```json
{
  "skills": [
    {
      "name": "multi-agent-code-review",
      "path": "/path/to/skills/multi-agent-code-review",
      "trigger": "review"
    }
  ]
}
```

Then use:
```bash
codex review --pr 123
codex review --diff changes.patch
codex review --files src/
```

### With Opencode

Add to your `opencode.config.js` or project root:

```javascript
module.exports = {
  skills: [
    {
      name: 'multi-agent-code-review',
      path: './skills/multi-agent-code-review',
      command: 'review'
    }
  ]
}
```

Then use:
```bash
opencode review
opencode review --diff HEAD~1
opencode review --pr https://github.com/user/repo/pull/123
```

## Integration Patterns

### Direct Integration

For both Codex and Opencode, the skill provides agent prompts that can be loaded:

```python
from skills.multi_agent_code_review.main import CodeReviewTeam

team = CodeReviewTeam()

# Get all agent prompts for external orchestrator
prompts = team.get_agent_prompts()
# Returns: {
#   "lead-architect": "...",
#   "security-expert": "...",
#   ...
# }
```

### As a Subagent/Task

When using this skill within another agent system:

```python
# Launch parallel reviews
team = CodeReviewTeam()
report = team.review(
    code_diff=diff_content,
    pr_description=pr_description,
    context={"language": "python", "framework": "fastapi"}
)

# Output markdown report
print(report.markdown())
```

### GitHub Actions / CI

```yaml
name: Multi-Agent Code Review
on: [pull_request]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
        with:
          fetch-depth: 0
      
      - name: Get PR diff
        run: git diff origin/main...HEAD > changes.patch
      
      - name: Run Multi-Agent Review
        run: |
          python skills/multi-agent-code-review/main.py changes.patch
```

## Customization

### Modifying Agent Behavior

Edit `config.json` to enable/disable agents:

```json
{
  "agents": {
    "security-expert": {
      "enabled": true,
      "priority": 1
    },
    "junior-dev-simulator": {
      "enabled": false
    }
  }
}
```

### Custom Agent Prompts

Edit files in `prompts/` directory to customize agent behavior.

### Output Format

Control output in `config.json`:

```json
{
  "output": {
    "include_per_agent_details": true,
    "include_suggested_fixes": true,
    "max_findings_per_severity": 20
  }
}
```

## Output Interpretation

The report includes:

1. **Executive Summary** - Quick overview of findings
2. **Severity Breakdown** - Critical/High/Medium/Low counts
3. **Consensus Items** - Issues found by multiple agents (high confidence)
4. **Individual Findings** - Agent-specific observations
5. **Suggested Fixes** - Code suggestions with diffs

### Severity Levels

- **Critical** 🚨 - Security vulnerabilities, data loss risks
- **High** ⚠️ - Performance issues, major bugs, architectural flaws
- **Medium** - Maintainability issues, edge cases
- **Low** - Style suggestions, minor improvements

### Consensus Indicator

Issues marked as "consensus" were found by 2+ agents, indicating high-confidence problems.

## Troubleshooting

### Agents Not Running

Check `config.json` - ensure agents are enabled and paths are correct.

### Empty Reports

Verify the diff format. The skill expects standard git diff format.

### Performance Issues

Reduce `max_concurrent_agents` in config if hitting rate limits.

## Advanced Usage

### Filtering by Category

```python
report = team.review(code_diff)
critical_security = [
    f for f in report.findings 
    if f.severity == 'critical' and f.category == 'security'
]
```

### Custom Consensus Rules

```python
from consensus import ConsensusReporter

config = {'min_agreement': 3}  # Require 3+ agents to agree
reporter = ConsensusReporter(config)
```

### Exporting Results

```python
import json

report = team.review(code_diff)
with open('review-report.json', 'w') as f:
    json.dump(report.metadata, f, indent=2)
```
