"""
Multi-Agent Code Review Skill
Orchestrates 6 specialized agents to perform comprehensive code reviews.
Compatible with Codex, Opencode, and other AI coding agents.
"""

import json
import os
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed


@dataclass
class Finding:
    """Represents a single finding from an agent."""

    severity: str  # critical, high, medium, low
    category: str
    location: str
    description: str
    recommendation: str
    code_suggestion: Optional[str] = None
    agent: str = ""

    def to_dict(self) -> Dict:
        return {
            "severity": self.severity,
            "category": self.category,
            "location": self.location,
            "description": self.description,
            "recommendation": self.recommendation,
            "code_suggestion": self.code_suggestion,
            "agent": self.agent,
        }


@dataclass
class AgentReport:
    """Report from a single agent."""

    agent_name: str
    findings: List[Finding] = field(default_factory=list)
    summary: str = ""
    confidence: int = 0  # 0-100

    def to_dict(self) -> Dict:
        return {
            "agent_name": self.agent_name,
            "findings": [f.to_dict() for f in self.findings],
            "summary": self.summary,
            "confidence": self.confidence,
        }


@dataclass
class ConsensusReport:
    """Final consensus report aggregating all agent findings."""

    findings: List[Finding]
    consensus_items: List[Dict]
    summary: str
    metadata: Dict

    def markdown(self) -> str:
        """Generate markdown formatted report."""
        lines = []

        # Header
        lines.append("# Multi-Agent Code Review Report")
        lines.append("")

        # Executive Summary
        lines.append("## Executive Summary")
        lines.append(self.summary)
        lines.append("")

        # Findings by Severity
        severity_order = ["critical", "high", "medium", "low"]
        for sev in severity_order:
            sev_findings = [f for f in self.findings if f.severity == sev]
            if sev_findings:
                lines.append(f"## {sev.upper()} Issues ({len(sev_findings)})")
                lines.append("")
                for i, finding in enumerate(sev_findings, 1):
                    lines.append(f"### {i}. {finding.category}")
                    lines.append(f"**Location:** `{finding.location}`")
                    lines.append("")
                    lines.append(finding.description)
                    lines.append("")
                    lines.append(f"**Recommendation:** {finding.recommendation}")
                    if finding.code_suggestion:
                        lines.append("")
                        lines.append("**Suggested Fix:**")
                        lines.append("```")
                        lines.append(finding.code_suggestion)
                        lines.append("```")
                    lines.append("")

        # Consensus Items
        if self.consensus_items:
            lines.append("## Consensus Findings")
            lines.append("Issues agreed upon by multiple agents:")
            lines.append("")
            for item in self.consensus_items:
                lines.append(
                    f"- **{item.get('severity', 'N/A').upper()}**: {item.get('description', '')}"
                )
                if "agreed_by" in item:
                    lines.append(f"  - Agreed by: {', '.join(item['agreed_by'])}")
                lines.append("")

        return "\n".join(lines)


class Agent:
    """Base agent class for code review specialists."""

    def __init__(self, name: str, prompt_file: str, config: Dict):
        self.name = name
        self.config = config
        self.prompt = self._load_prompt(prompt_file)

    def _load_prompt(self, prompt_file: str) -> str:
        """Load system prompt from file."""
        skill_dir = os.path.dirname(os.path.abspath(__file__))
        prompts_dir = os.path.join(skill_dir, "prompts")
        filepath = os.path.join(prompts_dir, prompt_file)

        if os.path.exists(filepath):
            with open(filepath, "r") as f:
                return f.read()
        return f"You are a {self.name} performing code review."

    def review(self, code_diff: str, context: Optional[str] = None) -> AgentReport:
        """
        Perform code review.
        This method should be called by the orchestration framework (Codex/Opencode).
        Returns structured findings.
        """
        # In actual implementation, this would call the LLM with the prompt
        # For now, return structure that the framework will populate
        return AgentReport(
            agent_name=self.name,
            findings=[],
            summary=f"{self.name} review completed",
            confidence=80,
        )

    def get_system_prompt(self) -> str:
        """Get the system prompt for this agent."""
        return self.prompt


class CodeReviewTeam:
    """Orchestrates multiple agents for comprehensive code review."""

    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path)
        self.agents = self._initialize_agents()

    def _load_config(self, config_path: Optional[str]) -> Dict:
        """Load configuration file."""
        if config_path and os.path.exists(config_path):
            with open(config_path, "r") as f:
                return json.load(f)

        # Default config
        skill_dir = os.path.dirname(os.path.abspath(__file__))
        default_config = os.path.join(skill_dir, "config.json")
        if os.path.exists(default_config):
            with open(default_config, "r") as f:
                return json.load(f)

        return {}

    def _initialize_agents(self) -> List[Agent]:
        """Initialize all enabled agents."""
        agents = []
        agent_configs = self.config.get("agents", {})

        agent_files = {
            "lead-architect": "lead-architect.txt",
            "security-expert": "security-expert.txt",
            "performance-engineer": "performance-engineer.txt",
            "maintainability-guru": "maintainability-guru.txt",
            "edge-case-specialist": "edge-case-specialist.txt",
            "junior-dev-simulator": "junior-dev-simulator.txt",
        }

        for agent_name, agent_config in agent_configs.items():
            if agent_config.get("enabled", True):
                prompt_file = agent_files.get(agent_name, f"{agent_name}.txt")
                agents.append(Agent(agent_name, prompt_file, agent_config))

        return agents

    def review(
        self,
        code_diff: str,
        pr_description: Optional[str] = None,
        file_paths: Optional[List[str]] = None,
        context: Optional[Dict] = None,
    ) -> ConsensusReport:
        """
        Perform comprehensive multi-agent code review.

        Args:
            code_diff: The code changes to review (diff format)
            pr_description: Optional PR description for context
            file_paths: Optional list of files being reviewed
            context: Additional context (language, framework, etc.)

        Returns:
            ConsensusReport with all findings
        """
        # Run all agents
        agent_reports = []

        if self.config.get("runtime", {}).get("parallel_execution", True):
            # Parallel execution
            with ThreadPoolExecutor(
                max_workers=self.config.get("runtime", {}).get(
                    "max_concurrent_agents", 6
                )
            ) as executor:
                futures = {
                    executor.submit(
                        self._run_agent, agent, code_diff, pr_description, context
                    ): agent
                    for agent in self.agents
                }

                for future in as_completed(futures):
                    agent = futures[future]
                    try:
                        report = future.result()
                        agent_reports.append(report)
                    except Exception as e:
                        print(f"Agent {agent.name} failed: {e}")
        else:
            # Sequential execution
            for agent in self.agents:
                report = self._run_agent(agent, code_diff, pr_description, context)
                agent_reports.append(report)

        # Build consensus
        return self._build_consensus(agent_reports)

    def _run_agent(
        self,
        agent: Agent,
        code_diff: str,
        pr_description: Optional[str],
        context: Optional[Dict],
    ) -> AgentReport:
        """Run a single agent."""
        # The actual LLM call would be handled by the orchestration framework
        # This returns a structure that Codex/Opencode will populate
        return agent.review(code_diff, context)

    def _build_consensus(self, agent_reports: List[AgentReport]) -> ConsensusReport:
        """Build consensus from all agent reports."""
        all_findings = []

        for report in agent_reports:
            for finding in report.findings:
                finding.agent = report.agent_name
                all_findings.append(finding)

        # Sort by severity weight
        severity_weights = {"critical": 100, "high": 50, "medium": 25, "low": 10}
        all_findings.sort(
            key=lambda f: severity_weights.get(f.severity, 0), reverse=True
        )

        # Find consensus items (same issue found by multiple agents)
        consensus_items = self._find_consensus(all_findings)

        # Generate summary
        summary = self._generate_summary(all_findings, consensus_items)

        return ConsensusReport(
            findings=all_findings,
            consensus_items=consensus_items,
            summary=summary,
            metadata={
                "agents_run": len(agent_reports),
                "total_findings": len(all_findings),
                "critical_count": len(
                    [f for f in all_findings if f.severity == "critical"]
                ),
                "high_count": len([f for f in all_findings if f.severity == "high"]),
            },
        )

    def _find_consensus(self, findings: List[Finding]) -> List[Dict]:
        """Find issues agreed upon by multiple agents."""
        # Group findings by location and category
        grouped = {}
        for finding in findings:
            key = f"{finding.location}:{finding.category}"
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(finding)

        consensus = []
        min_agreement = self.config.get("consensus", {}).get("min_agreement", 2)

        for key, group in grouped.items():
            if len(group) >= min_agreement:
                consensus.append(
                    {
                        "severity": group[0].severity,
                        "category": group[0].category,
                        "location": group[0].location,
                        "description": group[0].description,
                        "agreed_by": list(set(f.agent for f in group)),
                        "agreement_count": len(group),
                    }
                )

        return consensus

    def _generate_summary(self, findings: List[Finding], consensus: List[Dict]) -> str:
        """Generate executive summary."""
        critical = len([f for f in findings if f.severity == "critical"])
        high = len([f for f in findings if f.severity == "high"])
        medium = len([f for f in findings if f.severity == "medium"])
        low = len([f for f in findings if f.severity == "low"])

        lines = [
            f"**Total Findings:** {len(findings)}",
            f"- Critical: {critical}",
            f"- High: {high}",
            f"- Medium: {medium}",
            f"- Low: {low}",
            f"",
            f"**Consensus Items:** {len(consensus)} issues agreed upon by multiple agents",
            f"",
        ]

        if critical > 0:
            lines.append(
                f"⚠️ **Action Required:** {critical} critical issues need immediate attention."
            )
        elif high > 0:
            lines.append(
                f"⚠️ **Action Required:** {high} high priority issues should be addressed before merge."
            )
        else:
            lines.append(
                f"✅ **Status:** No critical issues found. Review medium/low priority items."
            )

        return "\n".join(lines)

    def get_agent_prompts(self) -> Dict[str, str]:
        """Get all agent system prompts for external orchestrators."""
        return {agent.name: agent.get_system_prompt() for agent in self.agents}


def main():
    """CLI entry point for the skill."""
    import sys

    # Check if running under Codex/Opencode
    if len(sys.argv) > 1:
        code_diff = sys.argv[1]

        team = CodeReviewTeam()
        report = team.review(code_diff=code_diff)

        print(report.markdown())
    else:
        print("Usage: python main.py '<code_diff>'")
        print("Or integrate with Codex/Opencode as a skill")


if __name__ == "__main__":
    main()
