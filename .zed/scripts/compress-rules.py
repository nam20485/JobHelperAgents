#!/usr/bin/env python3
"""
Compress rule files to minimize token usage while retaining essential content.
Includes redundancy detection and consolidation strategies.
Usage: compress-rules.py <file-or-directory-path> [--redundancy]
"""

import sys
import re
from pathlib import Path
from collections import defaultdict, Counter


class RuleAnalyzer:
    """Analyze rules for compression and redundancy."""

    def __init__(self):
        self.rules = []
        self.phrases = defaultdict(list)
        self.concepts = defaultdict(list)

    def parse_rules(self, content: str) -> list:
        """Extract all rules from content."""
        rules = []
        for match in re.finditer(
            r'<rule\s+"id"="([^"]+)"\s+"use"="([^"]+)"(?:\s+"context"="([^"]*)")?[^>]*>\s*<description>([^<]+)</description>\s*<content>(.*?)</content>\s*</rule>',
            content,
            re.DOTALL,
        ):
            rule = {
                "id": match.group(1),
                "use": match.group(2),
                "context": match.group(3),
                "description": match.group(4).strip(),
                "content": match.group(5).strip(),
                "full_match": match.group(0),
            }
            rules.append(rule)
        return rules

    def extract_phrases(self, rules: list) -> dict:
        """Find repeated phrases across rules."""
        phrase_map = defaultdict(list)

        for rule in rules:
            content = rule["content"]
            # Extract 3-10 word phrases
            words = content.split()
            for i in range(len(words) - 2):
                for length in range(3, min(11, len(words) - i)):
                    phrase = " ".join(words[i : i + length])
                    if len(phrase) > 10:  # Only track meaningful phrases
                        phrase_map[phrase].append(rule["id"])

        # Return only repeated phrases
        return {p: ids for p, ids in phrase_map.items() if len(ids) > 1}

    def extract_concepts(self, rules: list) -> dict:
        """Identify semantic concepts across rules."""
        concepts = defaultdict(list)

        # Concept patterns
        patterns = {
            "mandatory": r"(mandatory|always|must|required)",
            "optional": r"(optional|conditional|when)",
            "external_ref": r"(\.zed/|\.md|link|reference)",
            "compression": r"(compress|reduce|token|minimize|efficiency)",
            "examples": r"(example|pattern|format)",
            "external_files": r"(file|\.md|directory)",
        }

        for rule in rules:
            content = (rule["content"] + " " + rule["description"]).lower()
            for concept, pattern in patterns.items():
                if re.search(pattern, content):
                    concepts[concept].append(rule["id"])

        return concepts

    def find_redundancy(self, rules: list) -> dict:
        """Identify redundant content and consolidation opportunities."""
        redundancy = {
            "repeated_phrases": {},
            "concept_overlap": {},
            "consolidation_suggestions": [],
        }

        # Find repeated phrases
        repeated_phrases = self.extract_phrases(rules)
        for phrase, rule_ids in repeated_phrases.items():
            if len(rule_ids) >= 2:
                redundancy["repeated_phrases"][phrase] = rule_ids

        # Find concept overlaps
        concepts = self.extract_concepts(rules)
        for concept, rule_ids in concepts.items():
            if len(rule_ids) > 2:
                redundancy["concept_overlap"][concept] = rule_ids

        # Suggest consolidations
        if redundancy["concept_overlap"].get("mandatory"):
            redundancy["consolidation_suggestions"].append(
                {
                    "type": "consolidate_mandatory",
                    "description": "Multiple mandatory enforcement rules could be consolidated",
                    "rules": redundancy["concept_overlap"].get("mandatory", []),
                    "action": 'Consider creating a "core-enforcement" rule that references common enforcement patterns',
                }
            )

        if redundancy["concept_overlap"].get("external_ref"):
            redundancy["consolidation_suggestions"].append(
                {
                    "type": "consolidate_references",
                    "description": "Multiple rules reference external files/examples",
                    "rules": redundancy["concept_overlap"].get("external_ref", []),
                    "action": 'Review if a "common-patterns" index rule would reduce duplication',
                }
            )

        return redundancy


def compress_rule_content(content: str) -> str:
    """Compress rule content while preserving meaning."""
    # Remove excessive whitespace
    content = re.sub(r"\n\s*\n\s*\n", "\n\n", content)

    # Condense verbose phrases
    replacements = {
        r"should be\s+": "",
        r"must\s+": "",
        r"It is recommended that\s+": "",
        r"Please ensure that\s+": "",
        r"According to\s+": "",
        r"In order to\s+": "To ",
        r"When you are\s+": "When ",
        r"In the event that\s+": "If ",
        r"has the ability to\s+": "can ",
        r"is able to\s+": "can ",
    }

    for pattern, repl in replacements.items():
        content = re.sub(pattern, repl, content, flags=re.IGNORECASE)

    return content.strip()


def optimize_rule_file(file_path: Path, detect_redundancy: bool = False) -> tuple:
    """Optimize a single rule file. Returns (processed_count, stats)."""
    try:
        with open(file_path, "r") as f:
            content = f.read()

        original_size = len(content)
        analyzer = RuleAnalyzer()
        rules = analyzer.parse_rules(content)

        if not rules:
            print(f"No rules found in {file_path}")
            return 0, {}

        # Compress content
        optimized = content
        for rule in rules:
            old_content = rule["content"]
            new_content = compress_rule_content(old_content)
            optimized = optimized.replace(
                f"<content>{old_content}</content>",
                f"<content>\n{new_content}\n  </content>",
            )

        with open(file_path, "w") as f:
            f.write(optimized)

        new_size = len(optimized)
        reduction_pct = (
            ((original_size - new_size) / original_size * 100)
            if original_size > 0
            else 0
        )

        stats = {
            "original_size": original_size,
            "new_size": new_size,
            "reduction_pct": reduction_pct,
            "rule_count": len(rules),
            "redundancy": None,
        }

        # Detect redundancy if requested
        if detect_redundancy:
            stats["redundancy"] = analyzer.find_redundancy(rules)

        return len(rules), stats

    except Exception as e:
        print(f"✗ Error processing {file_path}: {e}")
        return 0, {}


def print_compression_stats(file_path: Path, stats: dict):
    """Print compression statistics."""
    print(f"\n✓ {file_path}")
    print(f"  Rules: {stats['rule_count']}")
    print(
        f"  Size: {stats['original_size']} → {stats['new_size']} bytes ({stats['reduction_pct']:.1f}% reduction)"
    )


def print_redundancy_report(file_path: Path, redundancy: dict):
    """Print redundancy analysis report."""
    if not redundancy or not any(
        [
            redundancy.get("repeated_phrases"),
            redundancy.get("concept_overlap"),
            redundancy.get("consolidation_suggestions"),
        ]
    ):
        return

    print(f"\n📊 Redundancy Analysis: {file_path}")

    # Repeated phrases
    if redundancy.get("repeated_phrases"):
        print(f"\n  Repeated Phrases ({len(redundancy['repeated_phrases'])} found):")
        for phrase, rule_ids in list(redundancy["repeated_phrases"].items())[:5]:
            tokens = len(phrase.split())
            potential_savings = tokens * (len(rule_ids) - 1)
            print(
                f"    • [{potential_savings} tokens] '{phrase[:50]}...' in: {', '.join(rule_ids)}"
            )

    # Concept overlaps
    if redundancy.get("concept_overlap"):
        print(f"\n  Concept Overlaps ({len(redundancy['concept_overlap'])} found):")
        for concept, rule_ids in redundancy["concept_overlap"].items():
            print(f"    • {concept}: {', '.join(rule_ids)}")

    # Consolidation suggestions
    if redundancy.get("consolidation_suggestions"):
        print(f"\n  Consolidation Opportunities:")
        for suggestion in redundancy["consolidation_suggestions"]:
            print(f"    • {suggestion['type']}: {suggestion['description']}")
            print(f"      Affected: {', '.join(suggestion['rules'])}")
            print(f"      Suggestion: {suggestion['action']}")


def main():
    if len(sys.argv) < 2:
        print("Usage: compress-rules.py <file-or-directory-path> [--redundancy]")
        print("\nOptions:")
        print(
            "  --redundancy    Perform redundancy analysis and report (without modification)"
        )
        sys.exit(1)

    path = Path(sys.argv[1])
    detect_redundancy = "--redundancy" in sys.argv

    if not path.exists():
        print(f"Error: {path} does not exist")
        sys.exit(1)

    total_processed = 0
    total_stats = {"original_size": 0, "new_size": 0, "rule_count": 0, "files": 0}

    if path.is_file():
        processed, stats = optimize_rule_file(path, detect_redundancy)
        if processed > 0:
            print_compression_stats(path, stats)
            if stats["redundancy"]:
                print_redundancy_report(path, stats["redundancy"])
            total_processed += processed
            total_stats["files"] += 1
            total_stats["original_size"] += stats["original_size"]
            total_stats["new_size"] += stats["new_size"]
            total_stats["rule_count"] += stats["rule_count"]

    elif path.is_dir():
        for md_file in sorted(path.glob("**/*.md")):
            if "example" not in md_file.name.lower():
                processed, stats = optimize_rule_file(md_file, detect_redundancy)
                if processed > 0:
                    print_compression_stats(md_file, stats)
                    if stats["redundancy"]:
                        print_redundancy_report(md_file, stats["redundancy"])
                    total_processed += processed
                    total_stats["files"] += 1
                    total_stats["original_size"] += stats["original_size"]
                    total_stats["new_size"] += stats["new_size"]
                    total_stats["rule_count"] += stats["rule_count"]

    # Print summary
    if total_processed > 0:
        total_reduction = (
            (total_stats["original_size"] - total_stats["new_size"])
            / total_stats["original_size"]
            * 100
            if total_stats["original_size"] > 0
            else 0
        )
        print(f"\n{'=' * 60}")
        print(
            f"Summary: Optimized {total_stats['rule_count']} rules across {total_stats['files']} file(s)"
        )
        print(
            f"Total size: {total_stats['original_size']} → {total_stats['new_size']} bytes ({total_reduction:.1f}% reduction)"
        )
        print(f"{'=' * 60}")
    else:
        print("No rule files processed")


if __name__ == "__main__":
    main()
