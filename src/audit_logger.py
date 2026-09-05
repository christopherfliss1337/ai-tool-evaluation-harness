"""Audit Trail Logger - JSONL Decision Logging

Logs every classification decision to a JSONL file for audit, debugging,
and post-hoc analysis.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from .content_classifier import ClassificationResult


class AuditLogger:
    """JSONL audit trail logger for classification decisions

    Each log entry is a complete record of:
    - Input (content_id, timestamp)
    - Classification (result, confidence, evidence, rule)
    - Model performance (tokens, latency, cost)
    - Human escalation flag
    """

    def __init__(self, log_file: str = "logs/audit_trail.jsonl"):
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

    def log_classification(
        self,
        result: ClassificationResult,
        content_preview: Optional[str] = None,
        metadata: Optional[dict] = None,
    ):
        """Log a classification result to JSONL audit trail

        Args:
            result: ClassificationResult from ContentClassifier
            content_preview: Optional first 200 chars of content (for debugging)
            metadata: Optional additional metadata to log
        """
        # Build audit log entry
        log_entry = {
            # Core classification
            "content_id": result.content_id,
            "timestamp": result.timestamp.isoformat(),
            "classification": result.classification,
            "confidence": result.confidence,
            "reasoning": result.reasoning,
            "evidence": result.evidence,
            "applied_rule": result.applied_rule,

            # Model info
            "model_used": result.model_used,
            "prompt_variant": result.prompt_variant,

            # Performance metrics
            "input_tokens": result.input_tokens,
            "output_tokens": result.output_tokens,
            "latency_ms": result.latency_ms,
            "cost_usd": result.cost_usd,

            # Human escalation
            "escalate_to_human": result.escalate_to_human,
        }

        # Add content preview if provided (truncated for safety)
        if content_preview:
            log_entry["content_preview"] = content_preview[:200]

        # Add metadata if provided
        if metadata:
            log_entry["metadata"] = metadata

        # Append to JSONL file
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")

    def get_stats(self) -> dict:
        """Get statistics from audit log

        Returns:
            Dict with counts, averages, and cost totals
        """
        if not self.log_file.exists():
            return {
                "total_classifications": 0,
                "error": "No audit log found"
            }

        entries = []
        with open(self.log_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    entries.append(json.loads(line))

        if not entries:
            return {"total_classifications": 0}

        # Calculate statistics
        total = len(entries)
        harmful = sum(1 for e in entries if e["classification"] == "harmful")
        safe = sum(1 for e in entries if e["classification"] == "safe")
        escalated = sum(1 for e in entries if e["escalate_to_human"])

        total_cost = sum(e["cost_usd"] for e in entries)
        avg_latency = sum(e["latency_ms"] for e in entries) / total
        avg_confidence = sum(e["confidence"] for e in entries) / total

        return {
            "total_classifications": total,
            "harmful_count": harmful,
            "safe_count": safe,
            "escalated_to_human": escalated,
            "escalation_rate": escalated / total if total > 0 else 0,
            "total_cost_usd": total_cost,
            "avg_latency_ms": avg_latency,
            "avg_confidence": avg_confidence,
            "cost_per_classification": total_cost / total if total > 0 else 0,
        }

    def get_recent(self, n: int = 10) -> list:
        """Get the N most recent audit log entries

        Args:
            n: Number of entries to return

        Returns:
            List of recent log entries (newest first)
        """
        if not self.log_file.exists():
            return []

        entries = []
        with open(self.log_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    entries.append(json.loads(line))

        return entries[-n:][::-1]  # Last N, reversed

    def get_by_content_id(self, content_id: str) -> Optional[dict]:
        """Get audit log entry by content_id

        Args:
            content_id: Content ID to search for

        Returns:
            Log entry dict or None if not found
        """
        if not self.log_file.exists():
            return None

        with open(self.log_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    entry = json.loads(line)
                    if entry["content_id"] == content_id:
                        return entry

        return None

    def get_false_positives(self, expected_results: dict) -> list:
        """Find potential false positives by comparing to expected results

        Args:
            expected_results: Dict mapping content_id -> expected classification

        Returns:
            List of log entries that may be false positives
        """
        if not self.log_file.exists():
            return []

        false_positives = []

        with open(self.log_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    entry = json.loads(line)
                    content_id = entry["content_id"]

                    if content_id in expected_results:
                        expected = expected_results[content_id]
                        actual = entry["classification"]

                        # False positive: classified harmful but expected safe
                        if actual == "harmful" and expected == "safe":
                            false_positives.append(entry)

        return false_positives

    def get_false_negatives(self, expected_results: dict) -> list:
        """Find potential false negatives by comparing to expected results

        Args:
            expected_results: Dict mapping content_id -> expected classification

        Returns:
            List of log entries that may be false negatives
        """
        if not self.log_file.exists():
            return []

        false_negatives = []

        with open(self.log_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    entry = json.loads(line)
                    content_id = entry["content_id"]

                    if content_id in expected_results:
                        expected = expected_results[content_id]
                        actual = entry["classification"]

                        # False negative: classified safe but expected harmful
                        if actual == "safe" and expected == "harmful":
                            false_negatives.append(entry)

        return false_negatives

    def clear(self):
        """Clear audit log (use with caution!)"""
        if self.log_file.exists():
            self.log_file.unlink()


def main():
    """CLI demo of audit logger"""
    from rich.console import Console
    from rich.table import Table

    console = Console()

    # Initialize logger
    logger = AuditLogger()

    # Get stats
    stats = logger.get_stats()

    if stats["total_classifications"] == 0:
        console.print("[yellow]No audit log entries found.[/yellow]")
        console.print("\nRun classifications to generate audit log:")
        console.print("  python -m src.content_classifier")
        return

    # Display stats
    console.print("[bold cyan]Audit Trail Statistics[/bold cyan]\n")

    table = Table(show_header=False)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green", justify="right")

    table.add_row("Total Classifications", str(stats["total_classifications"]))
    table.add_row("Harmful", str(stats["harmful_count"]))
    table.add_row("Safe", str(stats["safe_count"]))
    table.add_row("Escalated to Human", str(stats["escalated_to_human"]))
    table.add_row("Escalation Rate", f"{stats['escalation_rate']:.1%}")
    table.add_row("", "")
    table.add_row("Avg Latency", f"{stats['avg_latency_ms']:.0f} ms")
    table.add_row("Avg Confidence", f"{stats['avg_confidence']:.3f}")
    table.add_row("Total Cost", f"${stats['total_cost_usd']:.4f}")
    table.add_row("Cost per Classification", f"${stats['cost_per_classification']:.6f}")

    console.print(table)

    # Show recent entries
    console.print("\n[bold cyan]Recent Classifications (last 5):[/bold cyan]\n")

    recent = logger.get_recent(5)
    for entry in recent:
        console.print(
            f"[dim]{entry['content_id']}[/dim] → "
            f"[{'red' if entry['classification'] == 'harmful' else 'green'}]"
            f"{entry['classification'].upper()}[/] "
            f"(confidence: {entry['confidence']:.2f})"
        )
        if entry.get("content_preview"):
            console.print(f"  [dim]{entry['content_preview'][:100]}...[/dim]")


if __name__ == "__main__":
    main()
