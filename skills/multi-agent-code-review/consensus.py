"""
Consensus Builder Module
Aggregates findings from multiple agents with intelligent deduplication.

This module is language/framework agnostic and uses fuzzy matching
and fingerprinting to identify duplicate findings across agents.
"""

from typing import List, Dict, Any, Optional, Tuple, Set
from collections import defaultdict
from difflib import SequenceMatcher
import hashlib
import re


class FingerprintGenerator:
    """Generates fingerprints for findings to enable deduplication."""

    @staticmethod
    def normalize_text(text: str) -> str:
        """Normalize text for comparison."""
        # Convert to lowercase
        text = text.lower()
        # Remove extra whitespace
        text = re.sub(r"\s+", " ", text)
        # Remove punctuation
        text = re.sub(r"[^\w\s]", "", text)
        return text.strip()

    @staticmethod
    def generate_finding_fingerprint(finding: Dict[str, Any]) -> str:
        """
        Generate a fingerprint for a finding.

        Combines location, category, and normalized description.
        """
        location = finding.get("location", "")
        category = finding.get("category", "")
        description = finding.get("description", "")

        # Normalize description (first 150 chars)
        normalized_desc = FingerprintGenerator.normalize_text(description)[:150]

        # Create composite string
        content = f"{location}:{category}:{normalized_desc}"

        # Generate hash
        return hashlib.md5(content.encode()).hexdigest()[:16]

    @staticmethod
    def calculate_similarity(
        finding1: Dict[str, Any], finding2: Dict[str, Any]
    ) -> float:
        """
        Calculate similarity between two findings (0.0 to 1.0).

        Uses multiple signals:
        - Location matching
        - Category matching
        - Description text similarity
        """
        scores = []

        # Location similarity (30% weight)
        loc1 = finding1.get("location", "")
        loc2 = finding2.get("location", "")
        if loc1 and loc2:
            loc_sim = FingerprintGenerator._location_similarity(loc1, loc2)
            scores.append((loc_sim, 0.30))

        # Category match (20% weight)
        cat1 = finding1.get("category", "")
        cat2 = finding2.get("category", "")
        if cat1 and cat2:
            cat_match = 1.0 if cat1 == cat2 else 0.0
            scores.append((cat_match, 0.20))

        # Description similarity (40% weight)
        desc1 = finding1.get("description", "")
        desc2 = finding2.get("description", "")
        if desc1 and desc2:
            desc_sim = FingerprintGenerator._text_similarity(desc1, desc2)
            scores.append((desc_sim, 0.40))

        # Severity match (10% weight)
        sev1 = finding1.get("severity", "")
        sev2 = finding2.get("severity", "")
        if sev1 and sev2:
            sev_match = 1.0 if sev1 == sev2 else 0.0
            scores.append((sev_match, 0.10))

        # Calculate weighted average
        if not scores:
            return 0.0

        total_weight = sum(weight for _, weight in scores)
        weighted_sum = sum(score * weight for score, weight in scores)

        return weighted_sum / total_weight if total_weight > 0 else 0.0

    @staticmethod
    def _location_similarity(loc1: str, loc2: str) -> float:
        """Calculate similarity between two location strings."""
        # Split by colon to get file path
        file1 = loc1.split(":")[0] if ":" in loc1 else loc1
        file2 = loc2.split(":")[0] if ":" in loc2 else loc2

        # If files match, high similarity
        if file1 == file2:
            # Check if line numbers overlap
            lines1 = FingerprintGenerator._extract_line_numbers(loc1)
            lines2 = FingerprintGenerator._extract_line_numbers(loc2)

            if lines1 and lines2:
                # Calculate overlap
                overlap = len(set(lines1) & set(lines2))
                if overlap > 0:
                    return 1.0  # Same file and overlapping lines

            return 0.8  # Same file, no line overlap

        # Different files - check for similar names
        return FingerprintGenerator._text_similarity(file1, file2)

    @staticmethod
    def _extract_line_numbers(location: str) -> List[int]:
        """Extract line numbers from location string."""
        numbers = []
        # Match patterns like "file.py:45", "file.py:45-67", "file.py:45:67"
        matches = re.findall(r":(\d+)(?:[-:]?(\d+))?", location)
        for start, end in matches:
            start_num = int(start)
            end_num = int(end) if end else start_num
            numbers.extend(range(start_num, end_num + 1))
        return numbers

    @staticmethod
    def _text_similarity(text1: str, text2: str) -> float:
        """Calculate text similarity using SequenceMatcher."""
        if not text1 or not text2:
            return 0.0

        # Normalize
        t1 = FingerprintGenerator.normalize_text(text1)
        t2 = FingerprintGenerator.normalize_text(text2)

        return SequenceMatcher(None, t1, t2).ratio()


class ConsensusBuilder:
    """
    Builds consensus from multiple agent findings.

    Performs intelligent deduplication and identifies high-confidence
    issues found by multiple agents.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.fingerprinter = FingerprintGenerator()
        self.similarity_threshold = self.config.get("similarity_threshold", 0.75)
        self.min_agreement = self.config.get("min_agreement", 2)

    def build_consensus(
        self, findings: List[Any]
    ) -> Tuple[List[Dict[str, Any]], List[Any]]:
        """
        Build consensus from findings.

        Args:
            findings: List of Finding objects or dictionaries

        Returns:
            Tuple of (consensus_items, deduplicated_findings)
            - consensus_items: List of dicts with is_consensus=True
            - deduplicated_findings: List of Finding objects (merged duplicates)
        """
        # Convert to dicts if needed
        finding_dicts = []
        for f in findings:
            if hasattr(f, "to_dict"):
                finding_dicts.append(f.to_dict())
            elif isinstance(f, dict):
                finding_dicts.append(f)

        if not finding_dicts:
            return [], []

        # Group similar findings
        groups = self._group_similar_findings(finding_dicts)

        # Create consensus items and deduplicated findings
        consensus_items = []
        deduplicated = []

        for group in groups:
            if len(group) == 1:
                # Single finding - just add it
                deduplicated.append(self._create_finding_from_dict(group[0]))
            else:
                # Multiple similar findings - merge them
                merged = self._merge_findings(group)
                deduplicated.append(merged)

                # If meets consensus threshold, create consensus item
                if len(group) >= self.min_agreement:
                    consensus_item = self._create_consensus_item(group, merged)
                    consensus_items.append(consensus_item)

        # Sort by severity
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        consensus_items.sort(
            key=lambda x: severity_order.get(x.get("severity", "low"), 4)
        )

        return consensus_items, deduplicated

    def _group_similar_findings(
        self, findings: List[Dict[str, Any]]
    ) -> List[List[Dict]]:
        """
        Group similar findings together.

        Uses a two-phase approach:
        1. Quick fingerprint matching for exact duplicates
        2. Fuzzy similarity matching for near-duplicates
        """
        # Phase 1: Group by fingerprint
        fingerprint_groups = defaultdict(list)
        for finding in findings:
            fp = self.fingerprinter.generate_finding_fingerprint(finding)
            fingerprint_groups[fp].append(finding)

        # Phase 2: Merge groups based on fuzzy similarity
        merged_groups = []
        processed_fingerprints = set()

        fps = list(fingerprint_groups.keys())
        for i, fp1 in enumerate(fps):
            if fp1 in processed_fingerprints:
                continue

            group = fingerprint_groups[fp1].copy()
            processed_fingerprints.add(fp1)

            # Check against remaining groups
            for fp2 in fps[i + 1 :]:
                if fp2 in processed_fingerprints:
                    continue

                # Check if any finding in group1 is similar to any in group2
                if self._groups_similar(group, fingerprint_groups[fp2]):
                    group.extend(fingerprint_groups[fp2])
                    processed_fingerprints.add(fp2)

            merged_groups.append(group)

        return merged_groups

    def _groups_similar(self, group1: List[Dict], group2: List[Dict]) -> bool:
        """Check if two groups contain similar findings."""
        # Compare representative findings from each group
        # (first finding from each group)
        rep1 = group1[0]
        rep2 = group2[0]

        similarity = self.fingerprinter.calculate_similarity(rep1, rep2)
        return similarity >= self.similarity_threshold

    def _merge_findings(self, group: List[Dict]) -> Any:
        """
        Merge multiple similar findings into one.

        Takes the best attributes from all findings.
        """
        from main import Finding  # Import here to avoid circular dependency

        # Collect all agents
        agents = list(set(f.get("agent", "unknown") for f in group))

        # Use highest severity
        severity_priority = {"critical": 3, "high": 2, "medium": 1, "low": 0}
        base = max(
            group, key=lambda f: severity_priority.get(f.get("severity", "low"), 0)
        )

        # Collect unique recommendations
        recommendations = list(
            set(f.get("recommendation", "") for f in group if f.get("recommendation"))
        )

        # Collect unique code suggestions
        code_suggestions = list(
            set(f.get("code_suggestion", "") for f in group if f.get("code_suggestion"))
        )

        # Use best description (longest, most detailed)
        best_description = max(group, key=lambda f: len(f.get("description", ""))).get(
            "description", ""
        )

        # Calculate aggregate confidence
        avg_confidence = sum(f.get("confidence", 80) for f in group) / len(group)

        # Create merged finding
        return Finding(
            severity=base.get("severity", "low"),
            category=base.get("category", "general"),
            location=base.get("location", "unknown"),
            description=best_description,
            recommendation=recommendations[0] if recommendations else "",
            code_suggestion=code_suggestions[0] if code_suggestions else None,
            agent=f"consensus({len(agents)} agents)",
            confidence=int(avg_confidence),
            metadata={
                "merged_from": len(group),
                "contributing_agents": agents,
                "alternative_recommendations": recommendations[1:]
                if len(recommendations) > 1
                else [],
                "alternative_suggestions": code_suggestions[1:]
                if len(code_suggestions) > 1
                else [],
                "is_consensus": len(group) >= self.min_agreement,
            },
        )

    def _create_consensus_item(
        self, group: List[Dict], merged_finding: Any
    ) -> Dict[str, Any]:
        """Create a consensus item from a group of similar findings."""
        agents = list(set(f.get("agent", "unknown") for f in group))

        return {
            "severity": merged_finding.severity,
            "category": merged_finding.category,
            "location": merged_finding.location,
            "description": merged_finding.description,
            "recommendation": merged_finding.recommendation,
            "code_suggestion": merged_finding.code_suggestion,
            "agents": agents,
            "agreement_count": len(group),
            "confidence": merged_finding.confidence,
            "is_consensus": True,
            "findings_count": len(group),
        }

    def _create_finding_from_dict(self, finding_dict: Dict[str, Any]) -> Any:
        """Create a Finding object from a dictionary."""
        from main import Finding

        return Finding(
            severity=finding_dict.get("severity", "low"),
            category=finding_dict.get("category", "general"),
            location=finding_dict.get("location", "unknown"),
            description=finding_dict.get("description", ""),
            recommendation=finding_dict.get("recommendation", ""),
            code_suggestion=finding_dict.get("code_suggestion"),
            agent=finding_dict.get("agent", "unknown"),
            confidence=finding_dict.get("confidence", 80),
            metadata=finding_dict.get("metadata", {}),
        )


class ReportGenerator:
    """
    Generates formatted reports from consensus data.

    Produces both markdown and structured output formats.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

    def generate(self, report: Any) -> str:
        """
        Generate markdown report.

        Args:
            report: ConsensusReport object

        Returns:
            Markdown formatted string
        """
        lines = []

        # Header
        lines.append("# Multi-Agent Code Review Report")
        lines.append("")

        # Metadata
        if hasattr(report, "generated_at"):
            lines.append(f"*Generated: {report.generated_at}*")
            lines.append("")

        # Executive Summary
        lines.append("## Executive Summary")
        lines.append(report.summary)
        lines.append("")

        # Get findings by severity
        severity_findings = self._group_by_severity(report.findings)

        # Critical Issues
        if severity_findings["critical"]:
            lines.append(
                f"## 🚨 Critical Issues ({len(severity_findings['critical'])})"
            )
            lines.append("")
            lines.append(
                "These issues require immediate attention and must be fixed before merge."
            )
            lines.append("")
            for i, finding in enumerate(severity_findings["critical"], 1):
                lines.extend(self._format_finding(finding, i))
            lines.append("")

        # High Issues
        if severity_findings["high"]:
            lines.append(
                f"## ⚠️ High Priority Issues ({len(severity_findings['high'])})"
            )
            lines.append("")
            lines.append("These issues should be addressed before merge.")
            lines.append("")
            for i, finding in enumerate(severity_findings["high"], 1):
                lines.extend(self._format_finding(finding, i))
            lines.append("")

        # Consensus Items
        if report.consensus_items:
            lines.append(f"## ✅ Consensus Findings ({len(report.consensus_items)})")
            lines.append("")
            lines.append(
                "These issues were identified by multiple agents and have high confidence:"
            )
            lines.append("")
            for item in report.consensus_items:
                lines.extend(self._format_consensus_item(item))
            lines.append("")

        # Medium Issues
        if severity_findings["medium"]:
            count = len(severity_findings["medium"])
            show_count = min(count, 10)
            lines.append(f"## ℹ️ Medium Priority Issues ({count})")
            lines.append("")
            for i, finding in enumerate(severity_findings["medium"][:show_count], 1):
                lines.extend(self._format_finding(finding, i))
            if count > show_count:
                lines.append(f"*... and {count - show_count} more*")
            lines.append("")

        # Low Issues
        if severity_findings["low"]:
            count = len(severity_findings["low"])
            show_count = min(count, 5)
            lines.append(f"## 💡 Suggestions ({count})")
            lines.append("")
            for i, finding in enumerate(severity_findings["low"][:show_count], 1):
                lines.extend(self._format_finding(finding, i))
            if count > show_count:
                lines.append(f"*... and {count - show_count} more*")
            lines.append("")

        # Statistics
        if hasattr(report, "review_stats") and report.review_stats:
            lines.append("## Review Statistics")
            lines.append("")
            stats = report.review_stats
            lines.append(
                f"- **Execution Time:** {stats.get('execution_time_seconds', 'N/A')}s"
            )
            lines.append(
                f"- **Agents:** {stats.get('agents_success', 0)}/{stats.get('agents_total', 0)} successful"
            )
            lines.append(f"- **Total Findings:** {len(report.findings)}")
            lines.append(f"- **Consensus Items:** {len(report.consensus_items)}")
            lines.append("")

        # Footer
        lines.append("---")
        lines.append("*Report generated by Multi-Agent Code Review Skill*")

        return "\n".join(lines)

    def _group_by_severity(self, findings: List[Any]) -> Dict[str, List[Any]]:
        """Group findings by severity."""
        groups = {"critical": [], "high": [], "medium": [], "low": []}
        for finding in findings:
            severity = (
                finding.severity
                if hasattr(finding, "severity")
                else finding.get("severity", "low")
            )
            if severity in groups:
                groups[severity].append(finding)
        return groups

    def _format_finding(self, finding: Any, index: int) -> List[str]:
        """Format a single finding."""
        lines = []

        # Extract attributes (handle both object and dict)
        if hasattr(finding, "to_dict"):
            f = finding.to_dict()
        else:
            f = finding

        category = f.get("category", "general").upper()
        location = f.get("location", "unknown")
        description = f.get("description", "")
        recommendation = f.get("recommendation", "")
        code_suggestion = f.get("code_suggestion")
        agent = f.get("agent", "unknown")
        confidence = f.get("confidence", 80)

        lines.append(f"### {index}. [{category}] {location}")
        lines.append(f"**Agent:** {agent} (confidence: {confidence}%)")
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

        # Show alternative recommendations if present
        metadata = f.get("metadata", {})
        alt_recs = metadata.get("alternative_recommendations", [])
        if alt_recs:
            lines.append("")
            lines.append("**Alternative Approaches:**")
            for rec in alt_recs:
                lines.append(f"- {rec}")

        lines.append("")
        return lines

    def _format_consensus_item(self, item: Dict[str, Any]) -> List[str]:
        """Format a consensus item."""
        lines = []

        severity = item.get("severity", "unknown").upper()
        category = item.get("category", "general").upper()
        description = item.get("description", "")
        agents = item.get("agents", [])
        count = item.get("agreement_count", len(agents))

        lines.append(f"### [{severity}] {category}")
        lines.append(f"**✅ {count} agents agree:** {', '.join(agents)}")
        lines.append("")
        lines.append(description)
        lines.append("")

        if item.get("recommendation"):
            lines.append(f"**Recommendation:** {item['recommendation']}")

        if item.get("code_suggestion"):
            lines.append("")
            lines.append("**Suggested Code:**")
            lines.append("```")
            lines.append(item["code_suggestion"])
            lines.append("```")

        lines.append("")
        return lines


# Convenience function for external use
def build_consensus(
    findings: List[Any], config: Optional[Dict[str, Any]] = None
) -> Tuple[List[Dict[str, Any]], List[Any]]:
    """
    Convenience function to build consensus from findings.

    Args:
        findings: List of Finding objects or dictionaries
        config: Optional configuration

    Returns:
        Tuple of (consensus_items, deduplicated_findings)
    """
    builder = ConsensusBuilder(config)
    return builder.build_consensus(findings)
