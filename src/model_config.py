"""
Model registry and pricing configuration.

Centralizes model identifiers and pricing so the harness can be repointed
at a new Claude generation by editing one file.

Catalog and pricing verified against official Anthropic documentation.
Source: https://platform.claude.com/docs/en/models/overview
        https://platform.claude.com/docs/en/about-claude/pricing
Verified: 2026-09-05
"""

from typing import Dict, Literal

ModelAlias = Literal["fast", "balanced", "premium"]

# Active models as of the verification date above.
MODEL_REGISTRY: Dict[ModelAlias, str] = {
    "fast": "claude-haiku-4-5-20251001",  # lowest latency / cost
    "balanced": "claude-sonnet-5",        # default working model
    "premium": "claude-opus-5",           # highest capability
}

# USD per million tokens. Units: MTok. Source date: 2026-09-05.
# Cache-write and cache-hit tiers are omitted; this harness does not use
# prompt caching, so billing here is base input + output only.
PRICING: Dict[str, Dict[str, float]] = {
    "claude-haiku-4-5-20251001": {"input": 1.00, "output": 5.00},
    "claude-sonnet-5": {"input": 2.00, "output": 10.00},
    "claude-opus-5": {"input": 5.00, "output": 25.00},
}

PRICING_SOURCE_DATE = "2026-09-05"


def get_model_id(alias: ModelAlias) -> str:
    """Resolve an alias ("fast"/"balanced"/"premium") to a model ID."""
    return MODEL_REGISTRY[alias]


def get_pricing(model: str) -> Dict[str, float]:
    """
    Return {"input", "output"} USD per million tokens for a model.

    Raises KeyError for unknown models rather than falling back to an
    unrelated model's rates, which would silently misreport cost.
    """
    if model not in PRICING:
        raise KeyError(
            f"No pricing for '{model}'. Known models: {list(PRICING)}. "
            f"Pricing last verified {PRICING_SOURCE_DATE}."
        )
    return PRICING[model]


def calculate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Total USD for one request."""
    p = get_pricing(model)
    return (input_tokens * p["input"] + output_tokens * p["output"]) / 1_000_000
