# Multi-Agent Code Review Skill

A robust, language-agnostic code review system that deploys 6 specialized agents working in parallel to analyze code changes from different perspectives. Agents convene for a final consensus report with ranked findings and concrete fix suggestions.

## Features

- **Language & Framework Agnostic** - Works with any programming language or framework
- **6 Specialized Agents** - Each with unique focus and expertise
- **Intelligent Consensus** - Fuzzy matching to identify duplicate findings across agents
- **Parallel Execution** - All agents run simultaneously for efficiency
- **Robust Error Handling** - Graceful degradation if individual agents fail
- **Severity Ranking** - Critical/High/Medium/Low with clear action items
- **Code Suggestions** - Language-agnostic pseudocode examples for fixes

## Team Roles

1. **Lead Architect** - Overall structure, scalability, design patterns, coupling
2. **Security Expert** - OWASP Top 10, injection, auth, secrets, supply-chain risks
3. **Performance Engineer** - Time/space complexity, bottlenecks, resource optimization
4. **Maintainability Guru** - Naming, documentation, SOLID principles, testability
5. **Edge-Case Specialist** - Nulls, boundaries, concurrency, i18n, scale scenarios
6. **Junior Dev Simulator** - Implicit assumptions, unclear intent, confusion points

## Quick Start

### With Opencode

```bash
# Review current changes
opencode --skill /path/to/multi-agent-code-review review

# Review specific files
opencode --skill /path/to/multi-agent-code-review review --files src/

# Review a diff file
opencode --skill /path/to/multi-agent-code-review review --diff changes.patch
```

### With Codex

```bash
# Add to .codex config, then:
codex review --skill multi-agent-code-review --pr 123
```

### With Claude Code

```bash
# Load the skill
claude --skill /path/to/multi-agent-code-review

# Use in conversation
"Review this code using all agents"
```

### Manual Execution

```bash
# Show skill info
python main.py --info

# Review a diff file
python main.py --diff changes.patch

# Review with context
python main.py --diff changes.patch --language python --framework fastapi

# JSON output
python main.py --diff changes.patch --output json --output-file report.json
```

### Programmatic Usage

```python
from skills.multi_agent_code_review.main import CodeReviewTeam, ReviewContext

# Create team
team = CodeReviewTeam()

# Review code
report = team.review(
    code_diff=diff_content,
    context=ReviewContext(
        language="python",
        framework="django",
        pr_description="Added user authentication"
    )
)

# Get markdown report
print(report.markdown())

# Get structured data
print(report.to_json())
```

## Architecture

```
multi-agent-code-review/
├── skill.json              # Skill metadata
├── config.json             # Agent configuration
├── main.py                 # Orchestrator & data models
├── consensus.py            # Consensus builder with fuzzy matching
├── report_generator.py     # Markdown/JSON report generator
├── prompts/                # Agent system prompts
│   ├── lead-architect.txt
│   ├── security-expert.txt
│   ├── performance-engineer.txt
│   ├── maintainability-guru.txt
│   ├── edge-case-specialist.txt
│   └── junior-dev-simulator.txt
├── README.md               # This file
└── EXAMPLES.md             # Usage examples
```

## Configuration

Edit `config.json` to customize:

```json
{
  "agents": {
    "lead-architect": {
      "enabled": true,
      "priority": 1
    },
    "security-expert": {
      "enabled": true,
      "priority": 1
    }
  },
  "consensus": {
    "min_agreement": 2,
    "similarity_threshold": 0.75
  },
  "runtime": {
    "timeout_seconds": 300,
    "parallel_execution": true,
    "max_concurrent_agents": 6
  }
}
```

## Output Format

The skill generates a comprehensive markdown report:

```markdown
# Multi-Agent Code Review Report

## Executive Summary
- **Total Findings:** 12
- 🚨 Critical: 1
- ⚠️ High: 3
- ℹ️ Medium: 5
- 💡 Low: 3

## 🚨 Critical Issues (1)
### 1. [SECURITY] src/auth.ts:45
**Agent:** security-expert (confidence: 95%)
SQL injection vulnerability in user authentication...
[Code suggestion with fix]

## ✅ Consensus Findings (3)
These issues were identified by multiple agents:

### [HIGH] COMPLEXITY
**✅ 3 agents agree:** performance-engineer, lead-architect, maintainability-guru
Nested loop creates O(n²) complexity...

## Review Statistics
- **Execution Time:** 4.2s
- **Agents:** 6/6 successful
- **Consensus Items:** 3
```

## Language Agnostic Design

All agent prompts use **pseudocode and generic examples** instead of language-specific code:

```
// Instead of Python:
query = f"SELECT * FROM users WHERE name = '{username}'"

// Uses generic syntax:
function getUser(username) {
    query = "SELECT * FROM users WHERE name = " + username;  // VULNERABLE
}
```

This ensures the skill works equally well with:
- JavaScript/TypeScript
- Python
- Java/Kotlin
- Go/Rust/C/C++
- Ruby/PHP/Perl
- And any other language

## How It Works

1. **Input**: Code diff or plain text
2. **Parallel Analysis**: All 6 agents analyze simultaneously
3. **Validation**: Each finding is validated for correctness
4. **Deduplication**: Fuzzy matching identifies similar findings
5. **Consensus Building**: Issues found by multiple agents are flagged
6. **Ranking**: Findings sorted by severity (Critical → High → Medium → Low)
7. **Report Generation**: Markdown report with suggestions

## Severity Levels

- **Critical** 🚨 - Security vulnerabilities, data loss, crashes, infinite loops
- **High** ⚠️ - Performance issues, architectural flaws, major bugs
- **Medium** ℹ️ - Maintainability issues, edge cases, missing tests
- **Low** 💡 - Style suggestions, minor optimizations

## Integration Examples

See `EXAMPLES.md` for detailed integration examples with:
- GitHub Actions
- GitLab CI
- Pre-commit hooks
- IDE plugins
- Custom workflows

## Customization

### Adding a New Agent

1. Create `prompts/my-agent.txt`
2. Add to `config.json`:
   ```json
   "my-agent": {
     "enabled": true,
     "priority": 3,
     "focus_areas": ["my-area"]
   }
   ```

### Modifying Agent Behavior

Edit prompt files in `prompts/` directory. All prompts use language-agnostic examples.

### Custom Consensus Rules

Adjust in `config.json`:
- `min_agreement`: Agents needed for consensus (default: 2)
- `similarity_threshold`: Match sensitivity 0-1 (default: 0.75)

## Error Handling

The skill is designed to be resilient:

- If one agent fails, others continue
- Invalid findings are sanitized, not discarded
- Timeouts prevent hanging
- Clear error messages for debugging

## Performance

- Parallel execution of all agents
- Configurable timeouts
- Deduplication prevents redundant analysis
- Efficient fuzzy matching algorithm

## Contributing

To improve the skill:

1. Edit agent prompts in `prompts/`
2. Keep examples language-agnostic (pseudocode)
3. Test with multiple languages
4. Update documentation

## License

MIT - Free for personal and commercial use.
