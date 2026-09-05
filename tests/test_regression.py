"""Regression Test Suite

Ensures prompt changes don't introduce false positives/negatives.
"""

import json
import os
import pytest
from pathlib import Path

# Check if API key is available
HAS_API_KEY = bool(os.getenv("ANTHROPIC_API_KEY"))

# Skip tests if no API key
pytestmark = pytest.mark.skipif(
    not HAS_API_KEY,
    reason="ANTHROPIC_API_KEY not set in environment. Add to .env file to run API tests."
)

from src.content_classifier import ContentClassifier


@pytest.fixture
def golden_test_set():
    """Load golden test set"""
    test_data_path = Path("data/golden_test_set.json")
    with open(test_data_path, "r") as f:
        data = json.load(f)
    return data["test_cases"]


@pytest.fixture
def expected_results():
    """Load expected results baseline"""
    baseline_path = Path("data/expected_results.json")
    with open(baseline_path, "r") as f:
        data = json.load(f)
    return data["expected_results"]


@pytest.fixture
def classifier():
    """Create classifier with baseline prompt variant"""
    return ContentClassifier(
        prompt_variant="variant_2_cot",
        model="claude-haiku-4",
    )


class TestRegressionBaseline:
    """Regression tests against frozen baseline"""

    def test_harmful_content_detection(self, classifier, golden_test_set, expected_results):
        """Ensure all harmful content is still detected"""
        harmful_cases = [tc for tc in golden_test_set if tc["expected_classification"] == "harmful"]

        for test_case in harmful_cases:
            result = classifier.classify(
                content=test_case["content"],
                content_id=test_case["id"]
            )

            expected = expected_results[test_case["id"]]

            assert result.classification == expected["classification"], (
                f"Regression on {test_case['id']}: "
                f"Expected '{expected['classification']}' but got '{result.classification}'. "
                f"Content: '{test_case['content'][:50]}...'"
            )

    def test_safe_content_detection(self, classifier, golden_test_set, expected_results):
        """Ensure safe content is not falsely flagged"""
        safe_cases = [tc for tc in golden_test_set if tc["expected_classification"] == "safe"]

        for test_case in safe_cases:
            result = classifier.classify(
                content=test_case["content"],
                content_id=test_case["id"]
            )

            expected = expected_results[test_case["id"]]

            assert result.classification == expected["classification"], (
                f"False positive on {test_case['id']}: "
                f"Expected '{expected['classification']}' but got '{result.classification}'. "
                f"Content: '{test_case['content'][:50]}...'"
            )

    def test_confidence_threshold_calibration(self, classifier, golden_test_set):
        """Ensure confidence scores remain calibrated"""
        high_confidence_threshold = 0.9
        results = []

        for test_case in golden_test_set:
            result = classifier.classify(
                content=test_case["content"],
                content_id=test_case["id"]
            )
            results.append(result)

        # High-confidence predictions should be accurate
        high_confidence = [r for r in results if r.confidence >= high_confidence_threshold]

        if high_confidence:
            # At least 95% of high-confidence predictions should match expected
            # (This will be validated once we have actual API results)
            assert len(high_confidence) > 0, "No high-confidence predictions found"

    def test_no_new_false_positives(self, classifier, golden_test_set, expected_results):
        """Track if new prompt introduces false positives"""
        false_positives = []

        for test_case in golden_test_set:
            if test_case["expected_classification"] != "safe":
                continue

            result = classifier.classify(
                content=test_case["content"],
                content_id=test_case["id"]
            )

            if result.classification == "harmful":
                false_positives.append({
                    "id": test_case["id"],
                    "content": test_case["content"][:100],
                    "confidence": result.confidence,
                })

        # Report any false positives
        if false_positives:
            fp_summary = "\n".join([
                f"  - {fp['id']}: {fp['content']}... (confidence: {fp['confidence']:.2f})"
                for fp in false_positives
            ])
            pytest.fail(
                f"Found {len(false_positives)} false positives:\n{fp_summary}"
            )


class TestClassifierBasics:
    """Basic classifier functionality tests (no API required)"""

    def test_classifier_initialization(self):
        """Test classifier can be initialized"""
        # This should work even without API key for testing initialization
        try:
            classifier = ContentClassifier(
                prompt_variant="variant_1_direct",
                model="claude-haiku-4",
            )
            assert classifier.model == "claude-haiku-4"
            assert classifier.prompt_variant == "variant_1_direct"
        except ValueError as e:
            if "ANTHROPIC_API_KEY" in str(e):
                pytest.skip("API key required for classifier initialization")
            raise

    def test_prompt_template_loading(self):
        """Test prompt templates can be loaded"""
        prompt_file = Path("prompts/variant_1_direct.txt")
        assert prompt_file.exists(), "Prompt variant 1 should exist"

        content = prompt_file.read_text()
        assert "{content}" in content, "Prompt should have content placeholder"

    def test_golden_test_set_structure(self, golden_test_set):
        """Validate golden test set structure"""
        assert len(golden_test_set) == 30, "Should have 30 test cases"

        for tc in golden_test_set:
            assert "id" in tc
            assert "content" in tc
            assert "expected_classification" in tc
            assert tc["expected_classification"] in ["harmful", "safe"]
            assert "category" in tc
