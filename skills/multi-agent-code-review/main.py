"""
Multi-Agent Code Review Skill
A robust, language-agnostic orchestration system for comprehensive code reviews.

This skill coordinates multiple specialized agents to analyze code changes from
different perspectives, then aggregates their findings into a prioritized consensus report.

Compatible with: Codex, Opencode, Claude Code, and other AI coding agents.
Language/Framework Agnostic: Works with any programming language or framework.
"""

import json
import os
import sys
import hashlib
from typing import Dict, List, Optional, Any, Union, Set, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import traceback


# ============================================================================
# Data Models
# ============================================================================


@dataclass
class Finding:
    """
    Represents a single finding from an agent.

    Attributes:
        severity: critical|high|medium|low
        category: Type of issue found
        location: File path and line/function reference
        description: Detailed explanation of the issue
        recommendation: How to fix or improve
        code_suggestion: Optional code example (language-agnostic pseudocode)
        agent: Name of the agent that found this
        confidence: Agent's confidence score (0-100)
        metadata: Additional structured data
    """

    severity: str
    category: str
    location: str
    description: str
    recommendation: str
    code_suggestion: Optional[str] = None
    agent: str = ""
    confidence: int = 80
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate finding after creation."""
        valid_severities = {"critical", "high", "medium", "low"}
        if self.severity not in valid_severities:
            raise ValueError(
                f"Invalid severity: {self.severity}. Must be one of {valid_severities}"
            )

        if not 0 <= self.confidence <= 100:
            raise ValueError(f"Confidence must be 0-100, got {self.confidence}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return asdict(self)

    def get_fingerprint(self) -> str:
        """Generate a fingerprint for deduplication."""
        # Create hash based on location + category + normalized description
        normalized_desc = self.description.lower().strip()[:100]
        content = f"{self.location}:{self.category}:{normalized_desc}"
        return hashlib.md5(content.encode()).hexdigest()[:16]


@dataclass
class AgentReport:
    """
    Report from a single agent.

    Attributes:
        agent_name: Name of the agent
        findings: List of findings from this agent
        summary: High-level summary of the review
        confidence: Overall confidence score (0-100)
        execution_time_ms: Time taken to complete review
        status: success|error|timeout
        error_message: Error details if status is error
    """

    agent_name: str
    findings: List[Finding] = field(default_factory=list)
    summary: str = ""
    confidence: int = 0
    execution_time_ms: int = 0
    status: str = "success"
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "agent_name": self.agent_name,
            "findings": [f.to_dict() for f in self.findings],
            "summary": self.summary,
            "confidence": self.confidence,
            "execution_time_ms": self.execution_time_ms,
            "status": self.status,
            "error_message": self.error_message,
        }


@dataclass
class ReviewContext:
    """
    Context for the code review.

    All fields are optional to maintain language/framework agnosticism.
    """

    language: Optional[str] = None
    framework: Optional[str] = None
    repository: Optional[str] = None
    branch: Optional[str] = None
    pr_description: Optional[str] = None
    file_paths: Optional[List[str]] = None
    additional_context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConsensusReport:
    """
    Final consensus report aggregating all agent findings.

    Attributes:
        findings: All findings (deduplicated)
        consensus_items: Issues found by multiple agents
        summary: Executive summary
        metadata: Report metadata
        generated_at: Timestamp
        review_stats: Statistics about the review
    """

    findings: List[Finding]
    consensus_items: List[Dict[str, Any]]
    summary: str
    metadata: Dict[str, Any]
    generated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    review_stats: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "findings": [f.to_dict() for f in self.findings],
            "consensus_items": self.consensus_items,
            "summary": self.summary,
            "metadata": self.metadata,
            "generated_at": self.generated_at,
            "review_stats": self.review_stats,
        }

    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent, default=str)

    def markdown(self) -> str:
        """Generate markdown formatted report."""
        from report_generator import ReportGenerator

        generator = ReportGenerator()
        return generator.generate(self)


# ============================================================================
# Validation
# ============================================================================


class Validator:
    """Validates findings and reports."""

    VALID_SEVERITIES = {"critical", "high", "medium", "low"}
    VALID_CATEGORIES = {
        # Security
        "security",
        "injection",
        "authentication",
        "authorization",
        "secrets",
        "cryptography",
        "supply_chain",
        "validation",
        "owasp",
        # Architecture
        "architecture",
        "design_pattern",
        "scalability",
        "coupling",
        "data_flow",
        # Performance
        "performance",
        "complexity",
        "database",
        "memory",
        "io",
        "caching",
        "concurrency",
        # Maintainability
        "maintainability",
        "naming",
        "organization",
        "documentation",
        "solid",
        "testability",
        # Edge Cases
        "edge_case",
        "nulls",
        "boundary",
        "concurrency_race",
        "error_handling",
        "i18n",
        "scale",
        # General
        "general",
        "assumptions",
        "intent",
        "context",
        "mistakes",
        "testing",
    }

    @classmethod
    def validate_finding(cls, finding: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate a finding dictionary.

        Returns:
            (is_valid, list_of_errors)
        """
        errors = []

        # Required fields
        required = ["severity", "category", "location", "description", "recommendation"]
        for field in required:
            if field not in finding or not finding[field]:
                errors.append(f"Missing required field: {field}")

        if errors:
            return False, errors

        # Validate severity
        if finding["severity"] not in cls.VALID_SEVERITIES:
            errors.append(f"Invalid severity: {finding['severity']}")

        # Validate confidence if present
        confidence = finding.get("confidence", 80)
        if not isinstance(confidence, (int, float)) or not 0 <= confidence <= 100:
            errors.append(f"Confidence must be 0-100, got {confidence}")

        return len(errors) == 0, errors

    @classmethod
    def sanitize_finding(cls, finding: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize and normalize a finding.

        Ensures all fields are present with safe defaults.
        """
        sanitized = {
            "severity": finding.get("severity", "low"),
            "category": finding.get("category", "general"),
            "location": finding.get("location", "unknown"),
            "description": finding.get("description", ""),
            "recommendation": finding.get("recommendation", ""),
            "code_suggestion": finding.get("code_suggestion"),
            "agent": finding.get("agent", "unknown"),
            "confidence": max(0, min(100, finding.get("confidence", 80))),
            "metadata": finding.get("metadata", {}),
        }

        # Ensure severity is valid
        if sanitized["severity"] not in cls.VALID_SEVERITIES:
            sanitized["severity"] = "low"

        return sanitized


# ============================================================================
# Agent Management
# ============================================================================


class Agent:
    """
    Base agent class for code review specialists.

    This class is framework-agnostic and works with any orchestration system.
    """

    def __init__(self, name: str, prompt_file: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self.prompt = self._load_prompt(prompt_file)
        self.enabled = config.get("enabled", True)
        self.priority = config.get("priority", 1)

    def _load_prompt(self, prompt_file: str) -> str:
        """Load system prompt from file."""
        skill_dir = Path(__file__).parent
        prompts_dir = skill_dir / "prompts"
        filepath = prompts_dir / prompt_file

        try:
            if filepath.exists():
                return filepath.read_text(encoding="utf-8")
        except Exception as e:
            print(f"Warning: Could not load prompt for {self.name}: {e}")

        return f"You are a {self.name} performing code review."

    def review(
        self, code_diff: str, context: Optional[ReviewContext] = None
    ) -> AgentReport:
        """
        Perform code review.

        This is a template method - actual LLM calls are handled by the orchestration
        framework (Codex, Opencode, etc.). Returns a structured report that the
        framework will populate.

        Args:
            code_diff: The code changes to review (diff format)
            context: Optional review context

        Returns:
            AgentReport with findings
        """
        if not self.enabled:
            return AgentReport(
                agent_name=self.name,
                status="skipped",
                summary=f"{self.name} is disabled",
            )

        # Return structure for the orchestration framework to populate
        return AgentReport(
            agent_name=self.name,
            findings=[],
            summary=f"{self.name} review ready - awaiting execution by orchestrator",
            confidence=0,
            status="pending",
        )

    def get_system_prompt(self) -> str:
        """Get the system prompt for this agent."""
        return self.prompt

    def get_focus_areas(self) -> List[str]:
        """Get the focus areas for this agent."""
        return self.config.get("focus_areas", [])


# ============================================================================
# Orchestration
# ============================================================================


class CodeReviewTeam:
    """
    Orchestrates multiple agents for comprehensive code review.

    This class is completely language and framework agnostic.
    """

    def __init__(self, config_path: Optional[Union[str, Path]] = None):
        self.config = self._load_config(config_path)
        self.agents = self._initialize_agents()
        self.validator = Validator()

    def _load_config(self, config_path: Optional[Union[str, Path]]) -> Dict[str, Any]:
        """Load configuration with robust error handling."""
        # Default configuration
        default_config = {
            "skill_name": "multi-agent-code-review",
            "version": "1.0.0",
            "agents": {
                "lead-architect": {"enabled": True, "priority": 1},
                "security-expert": {"enabled": True, "priority": 1},
                "performance-engineer": {"enabled": True, "priority": 2},
                "maintainability-guru": {"enabled": True, "priority": 2},
                "edge-case-specialist": {"enabled": True, "priority": 3},
                "junior-dev-simulator": {"enabled": True, "priority": 3},
            },
            "severity_weights": {"critical": 100, "high": 50, "medium": 25, "low": 10},
            "consensus": {"min_agreement": 2, "similarity_threshold": 0.8},
            "runtime": {
                "timeout_seconds": 300,
                "parallel_execution": True,
                "max_concurrent_agents": 6,
            },
        }

        # Try to load from file
        if config_path:
            config_file = Path(config_path)
        else:
            skill_dir = Path(__file__).parent
            config_file = skill_dir / "config.json"

        try:
            if config_file.exists():
                with open(config_file, "r", encoding="utf-8") as f:
                    file_config = json.load(f)
                    # Merge with defaults
                    default_config.update(file_config)
        except Exception as e:
            print(f"Warning: Could not load config from {config_file}: {e}")
            print("Using default configuration.")

        return default_config

    def _initialize_agents(self) -> List[Agent]:
        """Initialize all enabled agents with robust error handling."""
        agents = []
        agent_configs = self.config.get("agents", {})

        # Map agent names to prompt files
        agent_prompt_files = {
            "lead-architect": "lead-architect.txt",
            "security-expert": "security-expert.txt",
            "performance-engineer": "performance-engineer.txt",
            "maintainability-guru": "maintainability-guru.txt",
            "edge-case-specialist": "edge-case-specialist.txt",
            "junior-dev-simulator": "junior-dev-simulator.txt",
        }

        for agent_name, agent_config in agent_configs.items():
            try:
                if agent_config.get("enabled", True):
                    prompt_file = agent_prompt_files.get(
                        agent_name, f"{agent_name}.txt"
                    )
                    agent = Agent(agent_name, prompt_file, agent_config)
                    agents.append(agent)
            except Exception as e:
                print(f"Warning: Failed to initialize agent {agent_name}: {e}")

        # Sort by priority
        agents.sort(key=lambda a: a.priority)

        return agents

    def review(
        self,
        code_diff: str,
        context: Optional[Union[ReviewContext, Dict[str, Any]]] = None,
    ) -> ConsensusReport:
        """
        Perform comprehensive multi-agent code review.

        This is the main entry point for the skill. It coordinates all agents
        and builds a consensus report.

        Args:
            code_diff: The code changes to review (diff format)
            context: Optional review context (ReviewContext object or dict)

        Returns:
            ConsensusReport with all findings
        """
        # Normalize context
        if isinstance(context, dict):
            context = ReviewContext(**context)
        elif context is None:
            context = ReviewContext()

        # Run all agents
        start_time = datetime.utcnow()
        agent_reports = self._execute_agents(code_diff, context)
        execution_time = (datetime.utcnow() - start_time).total_seconds()

        # Build consensus
        report = self._build_consensus(agent_reports, code_diff, context)

        # Add execution stats
        report.review_stats = {
            "execution_time_seconds": execution_time,
            "agents_total": len(self.agents),
            "agents_success": len([r for r in agent_reports if r.status == "success"]),
            "agents_error": len([r for r in agent_reports if r.status == "error"]),
        }

        return report

    def _execute_agents(
        self, code_diff: str, context: ReviewContext
    ) -> List[AgentReport]:
        """Execute all agents and collect reports."""
        agent_reports = []

        runtime_config = self.config.get("runtime", {})
        use_parallel = runtime_config.get("parallel_execution", True)
        max_workers = runtime_config.get("max_concurrent_agents", 6)
        timeout = runtime_config.get("timeout_seconds", 300)

        if use_parallel and len(self.agents) > 1:
            # Parallel execution
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {
                    executor.submit(
                        self._run_agent_with_timeout, agent, code_diff, context, timeout
                    ): agent
                    for agent in self.agents
                }

                for future in as_completed(futures):
                    agent = futures[future]
                    try:
                        report = future.result()
                        agent_reports.append(report)
                    except Exception as e:
                        agent_reports.append(
                            AgentReport(
                                agent_name=agent.name,
                                status="error",
                                error_message=str(e),
                                summary=f"Agent {agent.name} failed with error",
                            )
                        )
        else:
            # Sequential execution
            for agent in self.agents:
                try:
                    report = self._run_agent_with_timeout(
                        agent, code_diff, context, timeout
                    )
                    agent_reports.append(report)
                except Exception as e:
                    agent_reports.append(
                        AgentReport(
                            agent_name=agent.name,
                            status="error",
                            error_message=str(e),
                            summary=f"Agent {agent.name} failed with error",
                        )
                    )

        return agent_reports

    def _run_agent_with_timeout(
        self, agent: Agent, code_diff: str, context: ReviewContext, timeout: int
    ) -> AgentReport:
        """Run a single agent with timeout protection."""
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(agent.review, code_diff, context)
            try:
                return future.result(timeout=timeout)
            except concurrent.futures.TimeoutError:
                return AgentReport(
                    agent_name=agent.name,
                    status="timeout",
                    error_message=f"Agent timed out after {timeout} seconds",
                    summary=f"{agent.name} review timed out",
                )

    def _build_consensus(
        self, agent_reports: List[AgentReport], code_diff: str, context: ReviewContext
    ) -> ConsensusReport:
        """Build consensus from all agent reports."""
        from consensus import ConsensusBuilder

        # Collect and validate all findings
        all_findings = []
        for report in agent_reports:
            if report.status == "success":
                for finding in report.findings:
                    # Validate finding
                    is_valid, errors = self.validator.validate_finding(
                        finding.to_dict()
                    )
                    if is_valid:
                        all_findings.append(finding)
                    else:
                        # Try to sanitize
                        sanitized = self.validator.sanitize_finding(finding.to_dict())
                        all_findings.append(Finding(**sanitized))

        # Use consensus builder
        consensus_config = self.config.get("consensus", {})
        builder = ConsensusBuilder(consensus_config)

        consensus_items, deduplicated_findings = builder.build_consensus(all_findings)

        # Generate summary
        summary = self._generate_summary(deduplicated_findings, consensus_items)

        # Count by severity
        severity_counts = self._count_by_severity(deduplicated_findings)

        return ConsensusReport(
            findings=deduplicated_findings,
            consensus_items=consensus_items,
            summary=summary,
            metadata={
                "code_diff_length": len(code_diff),
                "agents_run": len(agent_reports),
                "successful_agents": len(
                    [r for r in agent_reports if r.status == "success"]
                ),
                "severity_counts": severity_counts,
                "context": {
                    "language": context.language,
                    "framework": context.framework,
                }
                if context
                else {},
            },
        )

    def _count_by_severity(self, findings: List[Finding]) -> Dict[str, int]:
        """Count findings by severity level."""
        counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for finding in findings:
            if finding.severity in counts:
                counts[finding.severity] += 1
        return counts

    def _generate_summary(self, findings: List[Finding], consensus: List[Dict]) -> str:
        """Generate executive summary."""
        counts = self._count_by_severity(findings)
        total = len(findings)

        lines = [
            f"**Total Findings:** {total}",
            f"",
            f"**By Severity:**",
            f"- 🚨 Critical: {counts['critical']}",
            f"- ⚠️ High: {counts['high']}",
            f"- ℹ️ Medium: {counts['medium']}",
            f"- 💡 Low: {counts['low']}",
            f"",
            f"**Consensus Items:** {len(consensus)} (issues confirmed by multiple agents)",
            f"",
        ]

        # Action items
        if counts["critical"] > 0:
            lines.append(
                f"🚨 **Immediate Action Required:** {counts['critical']} critical issues "
                f"need to be fixed before merge."
            )
        elif counts["high"] > 0:
            lines.append(
                f"⚠️ **Action Required:** {counts['high']} high priority issues "
                f"should be addressed before merge."
            )
        elif counts["medium"] > 0:
            lines.append(
                f"✅ **Review Recommended:** {counts['medium']} medium priority items to consider."
            )
        else:
            lines.append(
                f"✅ **Looks Good:** No critical issues found. Minor suggestions only."
            )

        if consensus:
            lines.append(f"")
            lines.append(f"**High Confidence Issues** (agreed by multiple agents):")
            for item in consensus[:5]:  # Top 5
                sev = item.get("severity", "unknown").upper()
                desc = item.get("description", "")[:80]
                agents = item.get("agreement_count", 0)
                lines.append(f"- [{sev}] {desc}... ({agents} agents)")

        return "\n".join(lines)

    def get_agent_prompts(self) -> Dict[str, str]:
        """Get all agent system prompts for external orchestrators."""
        return {
            agent.name: agent.get_system_prompt()
            for agent in self.agents
            if agent.enabled
        }

    def get_skill_info(self) -> Dict[str, Any]:
        """Get information about the skill and its agents."""
        return {
            "skill_name": self.config.get("skill_name", "multi-agent-code-review"),
            "version": self.config.get("version", "1.0.0"),
            "agents": [
                {
                    "name": agent.name,
                    "enabled": agent.enabled,
                    "priority": agent.priority,
                    "focus_areas": agent.get_focus_areas(),
                }
                for agent in self.agents
            ],
            "total_agents": len(self.agents),
            "enabled_agents": len([a for a in self.agents if a.enabled]),
        }


# ============================================================================
# CLI Entry Point
# ============================================================================


def main():
    """CLI entry point for the skill."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Multi-Agent Code Review Skill",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --diff changes.patch
  python main.py --diff changes.patch --language python
  python main.py --info
        """,
    )

    parser.add_argument(
        "--diff", type=str, help="Path to diff file or raw diff content"
    )
    parser.add_argument(
        "--language", type=str, help="Programming language (optional, for context)"
    )
    parser.add_argument(
        "--framework", type=str, help="Framework being used (optional, for context)"
    )
    parser.add_argument("--config", type=str, help="Path to custom configuration file")
    parser.add_argument(
        "--info", action="store_true", help="Show skill information and exit"
    )
    parser.add_argument(
        "--output",
        type=str,
        choices=["markdown", "json"],
        default="markdown",
        help="Output format",
    )
    parser.add_argument(
        "--output-file", type=str, help="Write output to file instead of stdout"
    )

    args = parser.parse_args()

    # Show info and exit
    if args.info:
        team = CodeReviewTeam(args.config)
        info = team.get_skill_info()
        print(json.dumps(info, indent=2))
        return

    # Require diff
    if not args.diff:
        parser.error("--diff is required (unless using --info)")

    # Load diff
    diff_path = Path(args.diff)
    if diff_path.exists():
        code_diff = diff_path.read_text(encoding="utf-8")
    else:
        # Assume it's raw diff content
        code_diff = args.diff

    # Create context
    context = ReviewContext(language=args.language, framework=args.framework)

    # Run review
    try:
        team = CodeReviewTeam(args.config)
        report = team.review(code_diff, context)

        # Generate output
        if args.output == "json":
            output = report.to_json()
        else:
            output = report.markdown()

        # Write output
        if args.output_file:
            Path(args.output_file).write_text(output, encoding="utf-8")
            print(f"Report written to {args.output_file}")
        else:
            print(output)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if os.environ.get("DEBUG"):
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
