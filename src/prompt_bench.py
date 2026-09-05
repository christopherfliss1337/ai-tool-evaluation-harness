"""Prompt Testing Bench - Systematic A/B Testing of Prompt Variants

CLI tool for running multiple prompt variants against golden test set
and comparing their performance.
"""

import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

from rich.console import Console
from rich.table import Table
from rich.progress import track

from .content_classifier import ContentClassifier, ClassificationResult


console = Console()


class PromptMetrics:
    """Metrics for a single prompt variant"""

    def __init__(self, variant_name: str):
        self.variant_name = variant_name
        self.true_positives = 0
        self.true_negatives = 0
        self.false_positives = 0
        self.false_negatives = 0
        self.total_latency_ms = 0.0
        self.total_cost_usd = 0.0
        self.results: List[ClassificationResult] = []

    def add_result(self, result: ClassificationResult, expected: str):
        """Add a classification result and update metrics"""
        self.results.append(result)
        self.total_latency_ms += result.latency_ms
        self.total_cost_usd += result.cost_usd

        # Update confusion matrix
        if result.classification == "harmful" and expected == "harmful":
            self.true_positives += 1
        elif result.classification == "safe" and expected == "safe":
            self.true_negatives += 1
        elif result.classification == "harmful" and expected == "safe":
            self.false_positives += 1
        elif result.classification == "safe" and expected == "harmful":
            self.false_negatives += 1

    @property
    def precision(self) -> float:
        """Precision: TP / (TP + FP)"""
        denominator = self.true_positives + self.false_positives
        if denominator == 0:
            return 0.0
        return self.true_positives / denominator

    @property
    def recall(self) -> float:
        """Recall: TP / (TP + FN)"""
        denominator = self.true_positives + self.false_negatives
        if denominator == 0:
            return 0.0
        return self.true_positives / denominator

    @property
    def f1_score(self) -> float:
        """F1 Score: Harmonic mean of Precision and Recall"""
        if self.precision + self.recall == 0:
            return 0.0
        return 2 * (self.precision * self.recall) / (self.precision + self.recall)

    @property
    def accuracy(self) -> float:
        """Overall accuracy: (TP + TN) / Total"""
        total = self.true_positives + self.true_negatives + self.false_positives + self.false_negatives
        if total == 0:
            return 0.0
        return (self.true_positives + self.true_negatives) / total

    @property
    def avg_latency_ms(self) -> float:
        """Average latency in milliseconds"""
        if not self.results:
            return 0.0
        return self.total_latency_ms / len(self.results)

    @property
    def avg_confidence(self) -> float:
        """Average confidence score"""
        if not self.results:
            return 0.0
        return sum(r.confidence for r in self.results) / len(self.results)

    @property
    def cost_per_1k(self) -> float:
        """Cost per 1000 classifications"""
        if not self.results:
            return 0.0
        return (self.total_cost_usd / len(self.results)) * 1000


class PromptBench:
    """Prompt Testing Bench for systematic variant comparison"""

    def __init__(self, test_data_path: str = "data/golden_test_set.json"):
        self.test_data_path = Path(test_data_path)
        self.test_cases = self._load_test_data()

    def _load_test_data(self) -> List[Dict]:
        """Load golden test set"""
        if not self.test_data_path.exists():
            raise FileNotFoundError(
                f"Test data not found: {self.test_data_path}\n"
                f"Expected golden test set at this location."
            )

        with open(self.test_data_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return data.get("test_cases", [])

    def run_variant(
        self,
        variant_name: str,
        model: str = "fast",
        verbose: bool = True,
    ) -> PromptMetrics:
        """Run one prompt variant against all test cases"""
        metrics = PromptMetrics(variant_name)

        # Initialize classifier
        try:
            classifier = ContentClassifier(
                prompt_variant=variant_name,
                model=model,
            )
        except FileNotFoundError as e:
            console.print(f"[red]Error:[/red] {e}")
            sys.exit(1)

        # Run all test cases
        if verbose:
            console.print(f"\n[bold cyan]Running {variant_name}[/bold cyan] with {model}...")

        iterator = track(self.test_cases, description="Classifying...") if verbose else self.test_cases

        for test_case in iterator:
            try:
                result = classifier.classify(
                    content=test_case["content"],
                    content_id=test_case["id"],
                )

                metrics.add_result(result, test_case["expected_classification"])

            except Exception as e:
                console.print(f"[red]Error on {test_case['id']}:[/red] {e}")
                continue

        return metrics

    def compare_variants(
        self,
        variant_names: List[str],
        model: str = "fast",
    ) -> Dict[str, PromptMetrics]:
        """Compare multiple prompt variants"""
        results = {}

        for variant in variant_names:
            results[variant] = self.run_variant(variant, model=model)

        return results

    def display_comparison(self, results: Dict[str, PromptMetrics]):
        """Display rich comparison table"""
        table = Table(title="Prompt Variant Comparison", show_header=True, header_style="bold magenta")

        table.add_column("Metric", style="cyan", no_wrap=True)
        for variant in results.keys():
            table.add_column(variant, justify="right")

        # Add metric rows
        metrics_to_show = [
            ("Precision", lambda m: f"{m.precision:.3f}"),
            ("Recall", lambda m: f"{m.recall:.3f}"),
            ("F1 Score", lambda m: f"{m.f1_score:.3f}"),
            ("Accuracy", lambda m: f"{m.accuracy:.3f}"),
            ("", lambda m: ""),  # Separator
            ("Avg Confidence", lambda m: f"{m.avg_confidence:.3f}"),
            ("Avg Latency (ms)", lambda m: f"{m.avg_latency_ms:.0f}"),
            ("Cost per 1K", lambda m: f"${m.cost_per_1k:.3f}"),
            ("Total Cost", lambda m: f"${m.total_cost_usd:.4f}"),
            ("", lambda m: ""),  # Separator
            ("True Positives", lambda m: str(m.true_positives)),
            ("True Negatives", lambda m: str(m.true_negatives)),
            ("False Positives", lambda m: str(m.false_positives)),
            ("False Negatives", lambda m: str(m.false_negatives)),
        ]

        for metric_name, metric_fn in metrics_to_show:
            row = [metric_name]
            for variant_metrics in results.values():
                row.append(metric_fn(variant_metrics))
            table.add_row(*row)

        console.print("\n")
        console.print(table)

        # Find best variant by F1 score
        best_variant = max(results.items(), key=lambda x: x[1].f1_score)
        console.print(
            f"\n[bold green]Best Variant:[/bold green] {best_variant[0]} "
            f"(F1: {best_variant[1].f1_score:.3f})"
        )

    def display_single_results(self, metrics: PromptMetrics):
        """Display results for a single variant"""
        table = Table(title=f"Results: {metrics.variant_name}", show_header=True, header_style="bold cyan")

        table.add_column("Metric", style="cyan", no_wrap=True)
        table.add_column("Value", justify="right", style="green")

        table.add_row("Precision", f"{metrics.precision:.3f}")
        table.add_row("Recall", f"{metrics.recall:.3f}")
        table.add_row("F1 Score", f"{metrics.f1_score:.3f}")
        table.add_row("Accuracy", f"{metrics.accuracy:.3f}")
        table.add_row("", "")
        table.add_row("Avg Confidence", f"{metrics.avg_confidence:.3f}")
        table.add_row("Avg Latency", f"{metrics.avg_latency_ms:.0f} ms")
        table.add_row("Cost per 1K", f"${metrics.cost_per_1k:.3f}")
        table.add_row("Total Cost", f"${metrics.total_cost_usd:.4f}")
        table.add_row("", "")
        table.add_row("True Positives", str(metrics.true_positives))
        table.add_row("True Negatives", str(metrics.true_negatives))
        table.add_row("False Positives", str(metrics.false_positives))
        table.add_row("False Negatives", str(metrics.false_negatives))

        console.print("\n")
        console.print(table)


def main():
    """CLI entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Prompt Testing Bench - Systematic prompt variant testing"
    )

    parser.add_argument(
        "command",
        choices=["run", "compare", "list"],
        help="Command to execute"
    )

    parser.add_argument(
        "--variant",
        help="Prompt variant name (e.g., variant_1_direct)"
    )

    parser.add_argument(
        "--variants",
        nargs="+",
        help="Multiple variants for comparison (e.g., variant_1_direct variant_2_cot)"
    )

    parser.add_argument(
        "--model",
        default="fast",
        help="Claude model to use (default: fast)"
    )

    parser.add_argument(
        "--test-data",
        default="data/golden_test_set.json",
        help="Path to golden test set (default: data/golden_test_set.json)"
    )

    args = parser.parse_args()

    # Initialize bench
    try:
        bench = PromptBench(test_data_path=args.test_data)
    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)

    console.print("[bold]AI Agent Quality Framework - Prompt Testing Bench[/bold]\n")

    # Execute command
    if args.command == "list":
        prompts_dir = Path("prompts")
        if not prompts_dir.exists():
            console.print("[red]Prompts directory not found[/red]")
            sys.exit(1)

        prompt_files = list(prompts_dir.glob("variant_*.txt"))
        console.print(f"[cyan]Available prompt variants ({len(prompt_files)}):[/cyan]")
        for pf in sorted(prompt_files):
            console.print(f"  • {pf.stem}")

    elif args.command == "run":
        if not args.variant:
            console.print("[red]Error:[/red] --variant required for 'run' command")
            sys.exit(1)

        metrics = bench.run_variant(args.variant, model=args.model)
        bench.display_single_results(metrics)

    elif args.command == "compare":
        if not args.variants:
            console.print("[red]Error:[/red] --variants required for 'compare' command")
            sys.exit(1)

        results = bench.compare_variants(args.variants, model=args.model)
        bench.display_comparison(results)


if __name__ == "__main__":
    main()
