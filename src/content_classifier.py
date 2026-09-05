"""Content Classification Agent with Anthropic Claude API

This module implements a content moderation classifier using Claude.
Supports multiple prompt variants and structured output via Pydantic.
"""

import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Literal, Optional

import anthropic
from dotenv import load_dotenv
from pydantic import BaseModel, Field

from .model_config import MODEL_REGISTRY, calculate_cost, get_pricing

# Load environment variables
load_dotenv()


class ClassificationResult(BaseModel):
    """Structured output from content classification"""

    content_id: str
    classification: Literal["harmful", "safe"]
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str
    evidence: list[str] = Field(default_factory=list)
    applied_rule: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    model_used: str
    prompt_variant: str
    escalate_to_human: bool = False

    # Performance metrics
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: float = 0.0
    cost_usd: float = 0.0


class ContentClassifier:
    """AI Agent for content moderation classification

    Uses Anthropic Claude API with configurable prompt variants.
    Includes confidence scoring, evidence tracking, and audit logging.
    """

    def __init__(
        self,
        prompt_variant: str = "variant_1_direct",
        model: str = "fast",  # Use model alias: "fast", "balanced", "premium"
        temperature: float = 0.0,
        max_tokens: int = 500,
        escalation_threshold: float = 0.75,
    ):
        """Initialize classifier with configuration

        Args:
            prompt_variant: Name of prompt file in prompts/ directory
            model: Model alias ("fast"/"balanced"/"premium") or full model ID
            temperature: Sampling temperature (0.0 = deterministic)
            max_tokens: Max output tokens
            escalation_threshold: Confidence below which to escalate to human
        """
        self.prompt_variant = prompt_variant

        # Resolve model alias to actual model ID
        if model in MODEL_REGISTRY:
            self.model = MODEL_REGISTRY[model]
        else:
            self.model = model  # Assume it's already a full model ID

        self.temperature = temperature
        self.max_tokens = max_tokens
        self.escalation_threshold = escalation_threshold

        # Initialize Anthropic client
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY not found in environment. "
                "Copy .env.example to .env and add your API key."
            )

        self.client = anthropic.Anthropic(api_key=api_key)

        # Load prompt template
        self.prompt_template = self._load_prompt_template(prompt_variant)

    def _load_prompt_template(self, variant: str) -> str:
        """Load prompt template from file"""
        prompt_file = Path(__file__).parent.parent / "prompts" / f"{variant}.txt"

        if not prompt_file.exists():
            raise FileNotFoundError(
                f"Prompt file not found: {prompt_file}\n"
                f"Available variants should be in prompts/ directory"
            )

        return prompt_file.read_text(encoding="utf-8")

    def _calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate API call cost in USD using centralized pricing"""
        try:
            return calculate_cost(self.model, input_tokens, output_tokens)
        except KeyError:
            # Model not in registry - return 0 to avoid breaking, log warning
            print(f"Warning: Model '{self.model}' not in pricing registry. Cost set to $0.00")
            return 0.0

    def _parse_classification_response(self, response_text: str) -> dict:
        """Parse JSON response from Claude

        Handles both clean JSON and JSON embedded in markdown code blocks.
        """
        # Strip markdown code blocks if present
        text = response_text.strip()
        if text.startswith("```json"):
            text = text[7:]  # Remove ```json
        if text.startswith("```"):
            text = text[3:]  # Remove ```
        if text.endswith("```"):
            text = text[:-3]  # Remove trailing ```

        text = text.strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            raise ValueError(
                f"Failed to parse JSON response: {e}\n"
                f"Response text: {text[:200]}..."
            )

    def classify(self, content: str, content_id: str = "unknown") -> ClassificationResult:
        """Classify content as harmful or safe

        Args:
            content: Text content to classify
            content_id: Unique identifier for this content

        Returns:
            ClassificationResult with classification, confidence, evidence, etc.
        """
        # Prepare prompt
        prompt = self.prompt_template.format(content=content)

        # Call Claude API with timing
        start_time = time.perf_counter()

        message = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            messages=[
                {"role": "user", "content": prompt}
            ],
        )

        latency_ms = (time.perf_counter() - start_time) * 1000

        # Extract response
        response_text = message.content[0].text

        # Parse JSON response
        classification_data = self._parse_classification_response(response_text)

        # Extract token usage
        input_tokens = message.usage.input_tokens
        output_tokens = message.usage.output_tokens

        # Calculate cost
        cost_usd = self._calculate_cost(input_tokens, output_tokens)

        # Determine human escalation
        confidence = classification_data.get("confidence", 0.5)
        escalate = (
            confidence < self.escalation_threshold or
            (classification_data.get("classification") == "harmful" and confidence < 0.85)
        )

        # Build result
        result = ClassificationResult(
            content_id=content_id,
            classification=classification_data.get("classification", "safe"),
            confidence=confidence,
            reasoning=classification_data.get("reasoning", ""),
            evidence=classification_data.get("evidence", []),
            applied_rule=classification_data.get("applied_rule"),
            model_used=self.model,
            prompt_variant=self.prompt_variant,
            escalate_to_human=escalate,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=latency_ms,
            cost_usd=cost_usd,
        )

        return result


def main():
    """CLI test of ContentClassifier"""
    print("AI Tool Evaluation Harness - Content Classifier Test\n")

    # Initialize classifier
    classifier = ContentClassifier(
        prompt_variant="variant_1_direct",
        model="fast",  # resolves via src/model_config.py
    )

    # Test content
    test_content = "This product will cure your cancer 100% guaranteed!"

    print(f"Classifying: '{test_content}'\n")

    # Classify
    result = classifier.classify(test_content, content_id="TEST_001")

    # Display result
    print(f"Classification: {result.classification.upper()}")
    print(f"Confidence: {result.confidence:.2f}")
    print(f"Reasoning: {result.reasoning}")
    if result.evidence:
        print(f"Evidence: {', '.join(result.evidence)}")
    print(f"Escalate to Human: {result.escalate_to_human}")
    print(f"\nPerformance:")
    print(f"  Latency: {result.latency_ms:.0f}ms")
    print(f"  Tokens: {result.input_tokens} in, {result.output_tokens} out")
    print(f"  Cost: ${result.cost_usd:.6f}")


if __name__ == "__main__":
    main()
