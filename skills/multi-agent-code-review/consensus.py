"""
Consensus Builder Module
Aggregates findings from multiple agents and builds consensus.
"""

from typing import List, Dict, Any, Optional
from collections import defaultdict
from difflib import SequenceMatcher


class FindingAggregator:
    """Aggregates and deduplicates findings from multiple agents."""

    def __init__(self, similarity_threshold: float = 0.8):
        self.similarity_threshold = similarity_threshold

    def aggregate(self, findings: List[Dict]) -> List[Dict]:
        """
        Aggregate findings, grouping similar issues together.

        Args:
            findings: List of finding dictionaries from all agents

        Returns:
            List of aggregated findings with agreement counts
        """
        if not findings:
            return []

        # Group by severity first
        by_severity = defaultdict(list)
        for finding in findings:
            severity = finding.get("severity", "low")
            by_severity[severity].append(finding)

        # Aggregate within each severity level
        aggregated = []
        for severity in ["critical", "high", "medium", "low"]:
            severity_findings = by_severity.get(severity, [])
            if severity_findings:
                aggregated.extend(self._aggregate_group(severity_findings))

        return aggregated

    def _aggregate_group(self, findings: List[Dict]) -> List[Dict]:
        """Aggregate a group of findings using similarity matching."""
        groups = []

        for finding in findings:
            matched = False
            for group in groups:
                if self._is_similar(finding, group[0]):
                    group.append(finding)
                    matched = True
                    break

            if not matched:
                groups.append([finding])

        # Convert groups to aggregated findings
        aggregated = []
        for group in groups:
            if len(group) == 1:
                # Single finding, add as-is
                aggregated.append(group[0])
            else:
                # Multiple similar findings - create consensus
                consensus = self._create_consensus_finding(group)
                aggregated.append(consensus)

        return aggregated

    def _is_similar(self, finding1: Dict, finding2: Dict) -> bool:
        """Check if two findings are similar enough to be the same issue."""
        # Check location similarity
        loc1 = finding1.get("location", "")
        loc2 = finding2.get("location", "")

        if loc1 and loc2:
            # Same file/function is strong indicator
            if self._location_match(loc1, loc2):
                # Check description similarity
                desc1 = finding1.get("description", "")
                desc2 = finding2.get("description", "")
                similarity = self._text_similarity(desc1, desc2)
                return similarity >= self.similarity_threshold

        return False

    def _location_match(self, loc1: str, loc2: str) -> bool:
        """Check if two locations match."""
        # Extract file path and line/function
        parts1 = loc1.split(":")
        parts2 = loc2.split(":")

        if parts1 and parts2:
            file1 = parts1[0]
            file2 = parts2[0]
            return file1 == file2

        return loc1 == loc2

    def _text_similarity(self, text1: str, text2: str) -> float:
        """Calculate text similarity ratio."""
        if not text1 or not text2:
            return 0.0

        return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()

    def _create_consensus_finding(self, group: List[Dict]) -> Dict:
        """Create a consensus finding from a group of similar findings."""
        # Use the most severe/highest priority finding as base
        base = group[0]

        # Collect all agents that found this
        agents = list(set(f.get("agent", "unknown") for f in group))

        # Merge recommendations (unique ones)
        recommendations = list(
            set(f.get("recommendation", "") for f in group if f.get("recommendation"))
        )

        # Create consensus finding
        consensus = {
            "severity": base.get("severity", "low"),
            "category": base.get("category", "unknown"),
            "location": base.get("location", ""),
            "description": base.get("description", ""),
            "recommendation": recommendations[0] if recommendations else "",
            "alternative_recommendations": recommendations[1:]
            if len(recommendations) > 1
            else [],
            "agents": agents,
            "agreement_count": len(group),
            "is_consensus": True,
            "original_findings": group,
        }

        # Add code suggestion if any finding has one
        for f in group:
            if f.get("code_suggestion"):
                consensus["code_suggestion"] = f["code_suggestion"]
                break

        return consensus


class ConsensusReporter:
    """Generates the final consensus report."""

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.aggregator = FindingAggregator(
            similarity_threshold=self.config.get("similarity_threshold", 0.8)
        )

    def build_report(
        self, agent_reports: List[Dict], code_diff: str, metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Build the final consensus report from all agent reports.

        Args:
            agent_reports: List of report dictionaries from each agent
            code_diff: The original code diff being reviewed
            metadata: Optional additional metadata

        Returns:
            Comprehensive consensus report
        """
        # Extract all findings
        all_findings = []
        for report in agent_reports:
            findings = report.get("findings", [])
            for finding in findings:
                finding["agent"] = report.get("agent_name", "unknown")
                all_findings.append(finding)

        # Aggregate findings
        aggregated = self.aggregator.aggregate(all_findings)

        # Separate consensus items
        consensus_items = [f for f in aggregated if f.get("is_consensus")]
        individual_items = [f for f in aggregated if not f.get("is_consensus")]

        # Sort by severity
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        consensus_items.sort(
            key=lambda x: severity_order.get(x.get("severity", "low"), 4)
        )
        individual_items.sort(
            key=lambda x: severity_order.get(x.get("severity", "low"), 4)
        )

        # Count by severity
        counts = self._count_by_severity(aggregated)

        # Generate summary
        summary = self._generate_summary(counts, consensus_items, individual_items)

        return {
            "summary": summary,
            "severity_counts": counts,
            "consensus_items": consensus_items,
            "individual_findings": individual_items,
            "all_findings": aggregated,
            "agent_count": len(agent_reports),
            "metadata": metadata or {},
            "code_diff_size": len(code_diff),
        }

    def _count_by_severity(self, findings: List[Dict]) -> Dict[str, int]:
        """Count findings by severity level."""
        counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for finding in findings:
            severity = finding.get("severity", "low")
            if severity in counts:
                counts[severity] += 1
        return counts

    def _generate_summary(
        self, counts: Dict[str, int], consensus: List[Dict], individual: List[Dict]
    ) -> str:
        """Generate executive summary."""
        total = sum(counts.values())

        lines = [
            f"**Total Findings:** {total}",
            f"",
            f"**By Severity:**",
            f"- Critical: {counts['critical']} ⚠️",
            f"- High: {counts['high']}",
            f"- Medium: {counts['medium']}",
            f"- Low: {counts['low']}",
            f"",
            f"**Consensus Items:** {len(consensus)} (issues confirmed by multiple agents)",
            f"**Individual Findings:** {len(individual)}",
            f"",
        ]

        # Action items
        if counts["critical"] > 0:
            lines.append(
                f"🚨 **Immediate Action Required:** {counts['critical']} critical issues need to be fixed before merge."
            )
        elif counts["high"] > 0:
            lines.append(
                f"⚠️ **Action Required:** {counts['high']} high priority issues should be addressed."
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

    def to_markdown(self, report: Dict[str, Any]) -> str:
        """Convert report to markdown format."""
        lines = []

        # Header
        lines.append("# Multi-Agent Code Review Report")
        lines.append("")

        # Summary
        lines.append("## Executive Summary")
        lines.append(report["summary"])
        lines.append("")

        # Critical Issues
        if report["severity_counts"]["critical"] > 0:
            critical = [
                f for f in report["all_findings"] if f.get("severity") == "critical"
            ]
            lines.append(f"## Critical Issues ({len(critical)}) 🚨")
            lines.append("")
            for i, finding in enumerate(critical, 1):
                lines.extend(self._format_finding(finding, i))
            lines.append("")

        # High Issues
        if report["severity_counts"]["high"] > 0:
            high = [f for f in report["all_findings"] if f.get("severity") == "high"]
            lines.append(f"## High Priority Issues ({len(high)}) ⚠️")
            lines.append("")
            for i, finding in enumerate(high, 1):
                lines.extend(self._format_finding(finding, i))
            lines.append("")

        # Consensus Items
        if report["consensus_items"]:
            lines.append(f"## Consensus Findings ({len(report['consensus_items'])})")
            lines.append("Issues agreed upon by multiple agents (high confidence):")
            lines.append("")
            for item in report["consensus_items"]:
                lines.extend(self._format_consensus_item(item))
            lines.append("")

        # Medium Issues
        if report["severity_counts"]["medium"] > 0:
            medium = [
                f for f in report["all_findings"] if f.get("severity") == "medium"
            ]
            lines.append(f"## Medium Priority Issues ({len(medium)})")
            lines.append("")
            for i, finding in enumerate(medium[:10], 1):  # Limit to first 10
                lines.extend(self._format_finding(finding, i))
            if len(medium) > 10:
                lines.append(f"*... and {len(medium) - 10} more*")
            lines.append("")

        # Low Issues
        if report["severity_counts"]["low"] > 0:
            low = [f for f in report["all_findings"] if f.get("severity") == "low"]
            lines.append(f"## Low Priority Suggestions ({len(low)})")
            lines.append("")
            for i, finding in enumerate(low[:5], 1):  # Limit to first 5
                lines.extend(self._format_finding(finding, i))
            if len(low) > 5:
                lines.append(f"*... and {len(low) - 5} more*")
            lines.append("")

        # Footer
        lines.append("---")
        lines.append(
            f"*Generated by Multi-Agent Code Review Skill | {report['agent_count']} agents | {report['severity_counts']['critical']} critical, {report['severity_counts']['high']} high*"
        )

        return "\n".join(lines)

    def _format_finding(self, finding: Dict, index: int) -> List[str]:
        """Format a single finding."""
        lines = []

        category = finding.get("category", "general")
        location = finding.get("location", "unknown")
        description = finding.get("description", "")
        recommendation = finding.get("recommendation", "")
        code_suggestion = finding.get("code_suggestion", "")
        agent = finding.get("agent", "unknown")

        lines.append(f"### {index}. [{category.upper()}] {location}")
        lines.append(f"**Agent:** {agent}")
        lines.append("")
        lines.append(description)
        lines.append("")
        lines.append(f"**Recommendation:** {recommendation}")

        if code_suggestion:
            lines.append("")
            lines.append("**Suggested Fix:**")
            lines.append("```")
            lines.append(code_suggestion)
            lines.append("```")

        lines.append("")
        return lines

    def _format_consensus_item(self, item: Dict) -> List[str]:
        """Format a consensus item."""
        lines = []

        severity = item.get("severity", "unknown")
        category = item.get("category", "general")
        description = item.get("description", "")
        agents = item.get("agents", [])
        count = item.get("agreement_count", len(agents))

        lines.append(f"### [{severity.upper()}] {category.upper()}")
        lines.append(f"**{count} agents agree:** {', '.join(agents)}")
        lines.append("")
        lines.append(description)
        lines.append("")

        # Show all recommendations
        main_rec = item.get("recommendation", "")
        alt_recs = item.get("alternative_recommendations", [])

        if main_rec:
            lines.append(f"**Primary Recommendation:** {main_rec}")

        if alt_recs:
            lines.append("")
            lines.append("**Alternative Approaches:**")
            for rec in alt_recs:
                lines.append(f"- {rec}")

        if item.get("code_suggestion"):
            lines.append("")
            lines.append("**Suggested Code:**")
            lines.append("```")
            lines.append(item["code_suggestion"])
            lines.append("```")

        lines.append("")
        return lines


def build_consensus(
    agent_reports: List[Dict], code_diff: str, config: Optional[Dict] = None
) -> str:
    """
    Convenience function to build consensus report from agent outputs.

    Args:
        agent_reports: List of agent report dictionaries
        code_diff: Original code diff
        config: Optional configuration

    Returns:
        Markdown formatted consensus report
    """
    reporter = ConsensusReporter(config)
    report = reporter.build_report(agent_reports, code_diff)
    return reporter.to_markdown(report)
