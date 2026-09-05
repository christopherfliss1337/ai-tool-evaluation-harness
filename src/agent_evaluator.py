"""Agent Evaluation Layer - Enhanced Classification with Audit

Wraps ContentClassifier with audit logging, batch processing,
and evaluation metrics.
"""

from typing import List, Optional
from pathlib import Path

from .content_classifier import ContentClassifier, ClassificationResult
from .audit_logger import AuditLogger


class AgentEvaluator:
    """Enhanced agent with evaluation and audit capabilities

    Combines ContentClassifier with AuditLogger for production use.
    """

    def __init__(
        self,
        prompt_variant: str = "variant_2_cot",
        model: str = "claude-haiku-4",
        escalation_threshold: float = 0.75,
        audit_log_file: str = "logs/audit_trail.jsonl",
        enable_audit: bool = True,
    ):
        """Initialize evaluator

        Args:
            prompt_variant: Prompt variant to use
            model: Claude model
            escalation_threshold: Confidence threshold for human escalation
            audit_log_file: Path to audit log file
            enable_audit: Whether to log to audit trail
        """
        self.classifier = ContentClassifier(
            prompt_variant=prompt_variant,
            model=model,
            escalation_threshold=escalation_threshold,
        )

        self.enable_audit = enable_audit
        if enable_audit:
            self.audit_logger = AuditLogger(log_file=audit_log_file)

    def classify_with_audit(
        self,
        content: str,
        content_id: str,
        metadata: Optional[dict] = None,
    ) -> ClassificationResult:
        """Classify content and log to audit trail

        Args:
            content: Content to classify
            content_id: Unique identifier
            metadata: Optional metadata to include in audit log

        Returns:
            ClassificationResult
        """
        # Classify
        result = self.classifier.classify(content, content_id)

        # Log to audit trail
        if self.enable_audit:
            self.audit_logger.log_classification(
                result=result,
                content_preview=content,
                metadata=metadata,
            )

        return result

    def batch_classify(
        self,
        items: List[dict],
        verbose: bool = True,
    ) -> List[ClassificationResult]:
        """Classify multiple items in batch

        Args:
            items: List of dicts with 'content' and 'id' keys
            verbose: Whether to print progress

        Returns:
            List of ClassificationResults
        """
        results = []

        if verbose:
            from rich.progress import track
            iterator = track(items, description="Classifying batch...")
        else:
            iterator = items

        for item in iterator:
            result = self.classify_with_audit(
                content=item["content"],
                content_id=item["id"],
                metadata=item.get("metadata"),
            )
            results.append(result)

        return results

    def evaluate_against_baseline(
        self,
        test_cases: List[dict],
        expected_results: dict,
    ) -> dict:
        """Evaluate against expected results

        Args:
            test_cases: List of test cases with 'id', 'content', 'expected_classification'
            expected_results: Dict mapping id -> expected classification

        Returns:
            Evaluation metrics dict
        """
        results = self.batch_classify(
            [{"content": tc["content"], "id": tc["id"]} for tc in test_cases]
        )

        # Calculate metrics
        tp = tn = fp = fn = 0

        for result, test_case in zip(results, test_cases):
            expected = expected_results.get(result.content_id, {}).get("classification")

            if result.classification == "harmful" and expected == "harmful":
                tp += 1
            elif result.classification == "safe" and expected == "safe":
                tn += 1
            elif result.classification == "harmful" and expected == "safe":
                fp += 1
            elif result.classification == "safe" and expected == "harmful":
                fn += 1

        # Calculate derived metrics
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        accuracy = (tp + tn) / len(test_cases) if test_cases else 0.0

        return {
            "total_cases": len(test_cases),
            "true_positives": tp,
            "true_negatives": tn,
            "false_positives": fp,
            "false_negatives": fn,
            "precision": precision,
            "recall": recall,
            "f1_score": f1,
            "accuracy": accuracy,
            "avg_confidence": sum(r.confidence for r in results) / len(results) if results else 0.0,
            "avg_latency_ms": sum(r.latency_ms for r in results) / len(results) if results else 0.0,
            "total_cost_usd": sum(r.cost_usd for r in results),
        }

    def get_audit_stats(self) -> dict:
        """Get audit trail statistics"""
        if not self.enable_audit:
            return {"error": "Audit logging not enabled"}

        return self.audit_logger.get_stats()


def main():
    """CLI demo"""
    import json
    from rich.console import Console
    from rich.table import Table

    console = Console()
    console.print("[bold cyan]Agent Evaluator Demo[/bold cyan]\n")

    # Load test data
    test_data_path = Path("data/golden_test_set.json")
    if not test_data_path.exists():
        console.print("[red]Golden test set not found at data/golden_test_set.json[/red]")
        return

    with open(test_data_path, "r") as f:
        test_data = json.load(f)

    # Load expected results
    baseline_path = Path("data/expected_results.json")
    if not baseline_path.exists():
        console.print("[red]Expected results not found at data/expected_results.json[/red]")
        return

    with open(baseline_path, "r") as f:
        baseline = json.load(f)

    # Initialize evaluator
    console.print("Initializing Agent Evaluator...")
    evaluator = AgentEvaluator(
        prompt_variant="variant_2_cot",
        model="claude-haiku-4",
    )

    # Run evaluation (only first 3 cases for demo)
    console.print("\n[yellow]Note:[/yellow] API key required to run classifications.")
    console.print("Add ANTHROPIC_API_KEY to .env file, then run:")
    console.print("  python -m src.agent_evaluator\n")


if __name__ == "__main__":
    main()
