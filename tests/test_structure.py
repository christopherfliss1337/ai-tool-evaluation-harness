"""Structure Tests - No API required

Tests that validate project structure and data integrity.
"""

import json
import pytest
from pathlib import Path


class TestProjectStructure:
    """Test project structure and files"""

    def test_prompt_variants_exist(self):
        """All three prompt variants should exist"""
        prompts_dir = Path("prompts")
        assert prompts_dir.exists(), "prompts/ directory should exist"

        variants = ["variant_1_direct", "variant_2_cot", "variant_3_few_shot"]
        for variant in variants:
            prompt_file = prompts_dir / f"{variant}.txt"
            assert prompt_file.exists(), f"{variant}.txt should exist"

            content = prompt_file.read_text()
            assert len(content) > 100, f"{variant} should have substantial content"
            assert "{content}" in content, f"{variant} should have {{content}} placeholder"

    def test_golden_test_set_complete(self):
        """Golden test set should have 30 well-formed cases"""
        test_data_path = Path("data/golden_test_set.json")
        assert test_data_path.exists(), "golden_test_set.json should exist"

        with open(test_data_path, "r") as f:
            data = json.load(f)

        assert "test_cases" in data
        assert data["total_cases"] == 30
        assert len(data["test_cases"]) == 30

        # Validate structure
        for tc in data["test_cases"]:
            assert "id" in tc, f"Test case missing id: {tc}"
            assert "content" in tc
            assert "expected_classification" in tc
            assert tc["expected_classification"] in ["harmful", "safe"]
            assert "category" in tc
            assert "reasoning" in tc

            # ID format
            assert tc["id"].startswith("TC"), f"ID should start with TC: {tc['id']}"

    def test_golden_test_set_balance(self):
        """Test set should be balanced (harmful vs safe)"""
        test_data_path = Path("data/golden_test_set.json")

        with open(test_data_path, "r") as f:
            data = json.load(f)

        harmful = sum(1 for tc in data["test_cases"] if tc["expected_classification"] == "harmful")
        safe = sum(1 for tc in data["test_cases"] if tc["expected_classification"] == "safe")

        # Test set should be reasonably balanced (allow 16/14 split)
        assert harmful + safe == 30, f"Should have 30 total cases"
        assert 14 <= harmful <= 16, f"Harmful cases should be 14-16, got {harmful}"
        assert 14 <= safe <= 16, f"Safe cases should be 14-16, got {safe}"

    def test_expected_results_baseline(self):
        """Expected results baseline should match test set"""
        baseline_path = Path("data/expected_results.json")
        assert baseline_path.exists(), "expected_results.json should exist"

        test_data_path = Path("data/golden_test_set.json")

        with open(baseline_path, "r") as f:
            baseline = json.load(f)

        with open(test_data_path, "r") as f:
            test_data = json.load(f)

        assert baseline["total_cases"] == 30
        assert len(baseline["expected_results"]) == 30

        # Verify all test case IDs are in baseline
        test_ids = {tc["id"] for tc in test_data["test_cases"]}
        baseline_ids = set(baseline["expected_results"].keys())

        assert test_ids == baseline_ids, "Baseline should cover all test cases"

    def test_requirements_files(self):
        """Requirements files should exist and have content"""
        req_file = Path("requirements.txt")
        assert req_file.exists(), "requirements.txt should exist"

        content = req_file.read_text()
        assert "anthropic" in content
        assert "pydantic" in content
        assert "pytest" in content
        assert "rich" in content

    def test_env_example_exists(self):
        """.env.example should exist with placeholder"""
        env_example = Path(".env.example")
        assert env_example.exists(), ".env.example should exist"

        content = env_example.read_text()
        assert "ANTHROPIC_API_KEY" in content
        assert "sk-ant-api03" in content, "Should have placeholder API key"

    def test_gitignore_configured(self):
        """.gitignore should exclude sensitive files"""
        gitignore = Path(".gitignore")
        assert gitignore.exists(), ".gitignore should exist"

        content = gitignore.read_text()
        assert ".env" in content, "Should ignore .env"
        assert "venv/" in content, "Should ignore venv"
        assert "__pycache__" in content, "Should ignore Python cache"


class TestCategoryDiversity:
    """Test that test cases cover diverse categories"""

    def test_hate_speech_coverage(self):
        """Should have multiple hate speech test cases"""
        test_data_path = Path("data/golden_test_set.json")

        with open(test_data_path, "r") as f:
            data = json.load(f)

        hate_speech = [tc for tc in data["test_cases"] if "hate_speech" in tc["category"]]
        assert len(hate_speech) >= 3, "Should have at least 3 hate speech test cases"

    def test_violence_coverage(self):
        """Should have violence/threat test cases"""
        test_data_path = Path("data/golden_test_set.json")

        with open(test_data_path, "r") as f:
            data = json.load(f)

        violence = [tc for tc in data["test_cases"] if "violence" in tc["category"]]
        assert len(violence) >= 2, "Should have at least 2 violence test cases"

    def test_health_misinfo_coverage(self):
        """Should have health misinformation test cases"""
        test_data_path = Path("data/golden_test_set.json")

        with open(test_data_path, "r") as f:
            data = json.load(f)

        health = [
            tc for tc in data["test_cases"]
            if "health" in tc["category"] and tc["expected_classification"] == "harmful"
        ]
        assert len(health) >= 3, "Should have at least 3 health misinfo test cases"

    def test_scam_coverage(self):
        """Should have scam/phishing test cases"""
        test_data_path = Path("data/golden_test_set.json")

        with open(test_data_path, "r") as f:
            data = json.load(f)

        scams = [
            tc for tc in data["test_cases"]
            if any(x in tc["category"] for x in ["scam", "phishing", "spam"])
        ]
        assert len(scams) >= 3, "Should have at least 3 scam test cases"

    def test_safe_content_diversity(self):
        """Safe content should cover multiple legitimate categories"""
        test_data_path = Path("data/golden_test_set.json")

        with open(test_data_path, "r") as f:
            data = json.load(f)

        safe_cases = [tc for tc in data["test_cases"] if tc["expected_classification"] == "safe"]
        categories = {tc["category"] for tc in safe_cases}

        assert len(categories) >= 5, f"Safe content should span multiple categories, got {len(categories)}"
