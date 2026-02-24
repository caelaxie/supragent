# Multi-Agent Code Review - Usage Examples

## Table of Contents

1. [Command Line Usage](#command-line-usage)
2. [Opencode Integration](#opencode-integration)
3. [Codex Integration](#codex-integration)
4. [Claude Code Integration](#claude-code-integration)
5. [CI/CD Integration](#cicd-integration)
6. [Programmatic Usage](#programmatic-usage)
7. [Custom Workflows](#custom-workflows)

---

## Command Line Usage

### Basic Usage

```bash
# Show skill information
python main.py --info

# Review a diff file
python main.py --diff changes.patch

# Review raw diff content
python main.py --diff "$(git diff HEAD~1)"

# With context
python main.py --diff changes.patch --language python --framework fastapi

# JSON output
python main.py --diff changes.patch --output json

# Save to file
python main.py --diff changes.patch --output-file report.md
```

### Advanced Options

```bash
# Custom configuration
python main.py --diff changes.patch --config my-config.json

# Review with full context
python main.py \
  --diff changes.patch \
  --language typescript \
  --framework react \
  --output markdown \
  --output-file review-report.md
```

---

## Opencode Integration

### Project-Level Configuration

Create `.opencode/config.yaml` in your project:

```yaml
skills:
  - name: multi-agent-code-review
    path: ./skills/multi-agent-code-review
    command: review
    
commands:
  review:
    description: "Run multi-agent code review"
    skill: multi-agent-code-review
```

### Usage

```bash
# Review current changes
opencode review

# Review specific files
opencode review --files src/

# Review PR
opencode review --pr https://github.com/user/repo/pull/123

# Review with options
opencode review --diff HEAD~3 --output json
```

### In Conversation

```
User: Review this code
Opencode: [loads multi-agent-code-review skill]
        [runs all 6 agents in parallel]
        [generates consensus report]

# You can also ask specific agents:
User: Security review of src/auth.js
Opencode: [runs only security-expert agent]
```

---

## Codex Integration

### Configuration File

Create `.codex` in your project root:

```json
{
  "skills": [
    {
      "name": "multi-agent-code-review",
      "path": "./skills/multi-agent-code-review",
      "triggers": ["review", "analyze", "check"]
    }
  ]
}
```

### Usage

```bash
# Review PR
codex review --pr 123

# Review specific files
codex review --files "src/**/*.ts"

# Review diff
codex review --diff changes.patch

# With custom config
codex review --config ./my-config.json
```

### In Session

```
> codex

You: Review the authentication code
Codex: [activates multi-agent-code-review skill]
       [analyzes with all 6 agents]
       [shows consensus report]
```

---

## Claude Code Integration

### Loading the Skill

```bash
# Start Claude Code with skill
claude --skill /path/to/multi-agent-code-review

# Or load dynamically
claude

# Then in conversation:
User: /load_skill /path/to/multi-agent-code-review
```

### Using the Skill

```
User: Review this pull request
Claude: [analyzes with all 6 agents]
       [shows findings by severity]
       [highlights consensus items]

User: Focus on security issues only
Claude: [runs only security-expert agent]
       [shows security findings]
```

### Project Configuration

Add to your `.claude/settings.json`:

```json
{
  "skills": [
    {
      "name": "multi-agent-code-review",
      "path": "./skills/multi-agent-code-review",
      "auto_load": true
    }
  ]
}
```

---

## CI/CD Integration

### GitHub Actions

```yaml
# .github/workflows/code-review.yml
name: Multi-Agent Code Review

on:
  pull_request:
    types: [opened, synchronize]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Get PR diff
        run: |
          git diff origin/${{ github.base_ref }}...HEAD > pr.diff

      - name: Run Multi-Agent Review
        run: |
          python skills/multi-agent-code-review/main.py \
            --diff pr.diff \
            --output markdown \
            --output-file review-report.md

      - name: Post Review Comment
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const report = fs.readFileSync('review-report.md', 'utf8');
            
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: report
            });
```

### GitLab CI

```yaml
# .gitlab-ci.yml
multi_agent_review:
  stage: review
  image: python:3.11
  script:
    - git diff origin/main...HEAD > mr.diff || true
    - |
      python skills/multi-agent-code-review/main.py \
        --diff mr.diff \
        --output markdown \
        --output-file review-report.md
    - cat review-report.md
  artifacts:
    reports:
      markdown: review-report.md
  only:
    - merge_requests
```

### Pre-commit Hook

```yaml
# .pre-commit-hooks.yaml
- id: multi-agent-review
  name: Multi-Agent Code Review
  entry: python skills/multi-agent-code-review/main.py
  language: python
  files: '\.(py|js|ts|java|go|rs)$'
  pass_filenames: false
  always_run: true
```

Or in your `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: local
    hooks:
      - id: multi-agent-review
        name: Multi-Agent Code Review
        entry: python skills/multi-agent-code-review/main.py --diff
        language: system
        pass_filenames: false
        always_run: true
        verbose: true
```

---

## Programmatic Usage

### Basic Example

```python
from skills.multi_agent_code_review.main import CodeReviewTeam, ReviewContext

# Initialize team
team = CodeReviewTeam()

# Simple review
with open('changes.patch', 'r') as f:
    code_diff = f.read()

report = team.review(code_diff)

# Print markdown report
print(report.markdown())

# Or get JSON
import json
print(report.to_json())
```

### With Context

```python
# Review with full context
context = ReviewContext(
    language="python",
    framework="django",
    repository="my-project",
    branch="feature/auth",
    pr_description="Added JWT authentication",
    file_paths=["src/auth.py", "src/middleware.py"]
)

report = team.review(code_diff, context)

# Access specific data
print(f"Critical issues: {report.review_stats}")
print(f"Consensus items: {len(report.consensus_items)}")
```

### Custom Configuration

```python
# Use custom config
team = CodeReviewTeam(config_path="custom-config.json")

# Or programmatically modify
from skills.multi_agent_code_review.main import CodeReviewTeam

team = CodeReviewTeam()
team.config["consensus"]["min_agreement"] = 3  # Require 3 agents to agree
team.config["runtime"]["timeout_seconds"] = 600  # 10 min timeout

report = team.review(code_diff)
```

### Processing Results

```python
# Filter findings
critical_security = [
    f for f in report.findings
    if f.severity == "critical" and f.category == "security"
]

# Get consensus items only
consensus_only = report.consensus_items

# Export to different formats
def export_to_sarif(report):
    """Convert to SARIF format for GitHub/CodeQL"""
    sarif = {
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "version": "2.1.0",
        "runs": [{
            "tool": {"driver": {"name": "multi-agent-code-review"}},
            "results": []
        }]
    }
    
    for finding in report.findings:
        sarif["runs"][0]["results"].append({
            "ruleId": finding.category,
            "level": finding.severity,
            "message": {"text": finding.description},
            "locations": [{"physicalLocation": {"artifactLocation": {"uri": finding.location}}}]
        })
    
    return sarif
```

### Using Individual Components

```python
from skills.multi_agent_code_review.consensus import ConsensusBuilder
from skills.multi_agent_code_review.main import Finding

# Build consensus manually
findings = [
    Finding(severity="high", category="security", ...),
    Finding(severity="high", category="security", ...),
]

builder = ConsensusBuilder({"min_agreement": 2})
consensus_items, deduplicated = builder.build_consensus(findings)

# Generate report
from skills.multi_agent_code_review.report_generator import ReportGenerator

generator = ReportGenerator()
markdown = generator.generate(report)
```

---

## Custom Workflows

### Selective Agent Execution

```python
# Run only specific agents
team = CodeReviewTeam()

# Disable some agents
for agent in team.agents:
    if agent.name not in ["security-expert", "lead-architect"]:
        agent.enabled = False

report = team.review(code_diff)
```

### Post-Processing Pipeline

```python
def custom_review_pipeline(code_diff, context):
    """Custom review with post-processing"""
    
    # Run review
    team = CodeReviewTeam()
    report = team.review(code_diff, context)
    
    # Filter by confidence
    high_confidence = [
        f for f in report.findings
        if f.confidence >= 90
    ]
    
    # Sort by location
    by_location = {}
    for finding in high_confidence:
        file = finding.location.split(":")[0]
        if file not in by_location:
            by_location[file] = []
        by_location[file].append(finding)
    
    # Generate custom report
    lines = ["# High Confidence Issues by File"]
    for file, findings in by_location.items():
        lines.append(f"\n## {file}")
        for f in findings:
            lines.append(f"- [{f.severity}] {f.category}: {f.description[:60]}...")
    
    return "\n".join(lines)
```

### Integration with Static Analysis

```python
import subprocess

def combined_review(code_diff):
    """Combine multi-agent review with static analysis"""
    
    # Run multi-agent review
    team = CodeReviewTeam()
    ma_report = team.review(code_diff)
    
    # Run static analyzer (e.g., pylint, eslint)
    static_results = subprocess.run(
        ["pylint", "--output-format=json", "src/"],
        capture_output=True,
        text=True
    )
    
    # Combine results
    all_findings = ma_report.findings + parse_static_results(static_results.stdout)
    
    # Build new consensus
    from skills.multi_agent_code_review.consensus import build_consensus
    consensus, deduped = build_consensus(all_findings)
    
    return deduped
```

### Batch Processing

```python
import os
from pathlib import Path

def batch_review(directory):
    """Review all .patch files in directory"""
    
    team = CodeReviewTeam()
    results = {}
    
    for patch_file in Path(directory).glob("*.patch"):
        print(f"Reviewing {patch_file}...")
        
        code_diff = patch_file.read_text()
        report = team.review(code_diff)
        
        # Save individual report
        output_file = patch_file.with_suffix(".md")
        output_file.write_text(report.markdown())
        
        # Track critical issues
        critical_count = len([f for f in report.findings if f.severity == "critical"])
        results[patch_file.name] = {
            "critical": critical_count,
            "total": len(report.findings)
        }
    
    # Summary
    print("\n=== Summary ===")
    for name, stats in results.items():
        print(f"{name}: {stats['critical']} critical, {stats['total']} total")
    
    return results
```

---

## Advanced Configuration

### Custom Severity Weights

```json
{
  "severity_weights": {
    "critical": 100,
    "high": 50,
    "medium": 25,
    "low": 10
  },
  "consensus": {
    "min_agreement": 2,
    "similarity_threshold": 0.8,
    "auto_escalate_critical": true
  }
}
```

### Agent Priorities

```json
{
  "agents": {
    "security-expert": {
      "enabled": true,
      "priority": 1,
      "focus_areas": ["owasp", "injection", "secrets"]
    },
    "performance-engineer": {
      "enabled": true,
      "priority": 2,
      "focus_areas": ["complexity", "memory", "io"]
    },
    "junior-dev-simulator": {
      "enabled": false  # Disable this agent
    }
  }
}
```

### Runtime Settings

```json
{
  "runtime": {
    "timeout_seconds": 300,
    "parallel_execution": true,
    "max_concurrent_agents": 6,
    "retry_failed_agents": true,
    "max_retries": 2
  }
}
```

---

## Tips & Best Practices

1. **Start with full review**: Run all 6 agents initially to get comprehensive feedback
2. **Focus on consensus**: Pay special attention to issues found by multiple agents
3. **Iterate**: Use findings to improve prompts for your specific codebase
4. **Customize**: Disable agents that aren't relevant to your project type
5. **Automate**: Integrate with CI/CD for consistent reviews
6. **Language agnostic**: The skill works with any language - no changes needed

---

## Troubleshooting

### Agents Not Running

Check `config.json` - ensure agents are enabled and paths are correct.

### Empty Reports

Verify the diff format. The skill expects standard git diff or unified diff format.

### Timeout Issues

Increase `timeout_seconds` in `config.json` for large diffs.

### Duplicate Findings

Adjust `similarity_threshold` in config (lower = more strict matching).

---

For more examples and advanced usage, see the test files and documentation in the skill directory.
