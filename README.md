# AI Tool Evaluation Harness

**Systematic framework for evaluating AI models, prompts, and classification agents**

Proof-of-work for Nature Heart application demonstrating: systematic evaluation methodology, prompt engineering, cost/quality trade-off analysis, and production-oriented patterns.

---

## What This Proves

✅ **Framework Implementation** - Complete evaluation harness with audit trails  
✅ **Offline Verification** - Structure tests passing (12/12)  
✅ **Evaluation Design** - 3 prompt strategies, golden test set, metrics framework  
⏸️ **Live Model Benchmark** - NOT executed (no authorized API evaluation)

This repository demonstrates evaluation infrastructure and methodology. Intentionally does not report fabricated benchmark results.

---

## Quick Start

### Prerequisites

- Python 3.12+
- Anthropic API key for live evaluation (optional - all tests run offline)

### Installation

```bash
git clone https://github.com/christopherfliss1337/ai-tool-evaluation-harness.git
cd ai-tool-evaluation-harness

# Create virtual environment
python -m venv venv

# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Optional: Configure API key for live testing
cp .env.example .env
# Edit .env and add ANTHROPIC_API_KEY
```

### Run Structure Tests

```bash
pytest tests/test_structure.py -v
```

Expected: 12/12 passing (offline, no API key required)

---

## Repository Structure

```
ai-tool-evaluation-harness/
├── src/
│   ├── content_classifier.py   # Core classification agent
│   ├── prompt_bench.py          # Prompt comparison CLI
│   ├── agent_evaluator.py       # Evaluation orchestration
│   └── audit_logger.py          # JSONL audit trail
│
├── prompts/
│   ├── variant_1_direct.txt     # Simple classification
│   ├── variant_2_cot.txt        # Structured reasoning
│   └── variant_3_few_shot.txt   # Example-based learning
│
├── data/
│   ├── golden_test_set.json     # 30 test cases (harmful/safe)
│   └── expected_results.json    # Baseline expectations
│
├── tests/
│   ├── test_structure.py        # 12 offline tests ✅
│   └── test_regression.py       # 7 API-dependent tests (pending key)
│
├── docs/
│   ├── case-study.md            # Framework documentation
│   └── evaluation-plan.md       # Evaluation methodology
│
└── logs/                        # Generated audit trails
```

---

## Core Components

### 1. Content Classifier

AI agent that classifies content as `harmful` or `safe` using Anthropic's Claude API.

**Features:**
- Structured output (Pydantic validation)
- Confidence scoring (0.0-1.0)
- Evidence extraction
- Human escalation logic for low-confidence + harmful combinations
- Token usage and cost tracking
- Audit trail generation

**Example:**

```python
from src.content_classifier import ContentClassifier

classifier = ContentClassifier(
    prompt_variant="variant_1_direct",
    model="fast"
)

result = classifier.classify(
    content="This product cures cancer 100% guaranteed!",
    content_id="TEST_001"
)

print(f"Classification: {result.classification}")
print(f"Confidence: {result.confidence}")
print(f"Escalate to human: {result.escalate_to_human}")
```

### 2. Prompt Bench

Systematic A/B testing framework for comparing prompt variants.

**Capabilities:**
- Run multiple prompts against golden test set
- Calculate precision, recall, F1, accuracy
- Measure latency and cost per classification
- Generate comparison reports
- Export JSONL audit trails

**Usage:**

```bash
# Compare all 3 variants (requires API key)
python -m src.prompt_bench compare --variants 1 2 3

# Run single variant
python -m src.prompt_bench run --variant 1 --output results.json
```

### 3. Evaluation Methodology

**Test Set:** 30 golden cases covering harmful/safe content  
**Metrics:** Precision, Recall, F1, Accuracy, Latency, Cost  
**Variants:** Direct, Chain-of-Thought, Few-Shot  

See [docs/case-study.md](docs/case-study.md) for detailed methodology.

---

## Testing

### Offline Tests (No API Key)

```bash
pytest tests/test_structure.py -v
```

Validates:
- Module imports
- Pydantic schema validation
- Configuration loading
- File structure integrity
- Prompt template syntax
- Golden test set format
- Cost calculation logic (offline)
- Escalation rule logic (offline)

**Status:** 12/12 passing

### API-Dependent Tests

```bash
# Requires ANTHROPIC_API_KEY in .env
pytest tests/test_regression.py -v
```

Validates:
- Actual API responses
- Model output parsing
- End-to-end classification pipeline
- Live latency/cost measurement

**Status:** 7/7 pending (requires API key setup)

---

## Security

```bash
# Run security scan
bandit -r src/ -f txt
```

**Status:** 0 issues (last verified: 2026-09-05)

**Security practices:**
- No hardcoded API keys
- Environment variable configuration
- Input validation via Pydantic
- No sensitive data in logs
- Gitignored secrets (.env, logs/)

---

## Current Limitations

**Intentional:**
- ⏸️ No live API benchmark results (no authorized evaluation executed)
- ⏸️ Golden test set is 30 curated cases — enough to exercise the harness, not a statistical benchmark
- ⏸️ Regression tests require an API key and are skipped by default

**By Design:**
- Framework demonstrates evaluation methodology, not production deployment
- Offline tests validate logic without API costs
- Clean separation: evaluation infrastructure vs. live results

---

## Documentation

**[docs/case-study.md](docs/case-study.md)**  
Framework architecture, design decisions, production-oriented patterns

**[docs/evaluation-plan.md](docs/evaluation-plan.md)**  
Evaluation methodology, metrics framework, expected performance characteristics

---

## Model Configuration

Model IDs and pricing live in one place: `src/model_config.py`.

```python
MODEL_REGISTRY = {
    "fast":     "claude-haiku-4-5-20251001",
    "balanced": "claude-sonnet-5",
    "premium":  "claude-opus-5",
}
```

Pass an alias (`"fast"`, `"balanced"`, `"premium"`) rather than a raw ID, so a new
Claude generation is a one-file change. Pricing carries an explicit source date and
raises on unknown models instead of silently falling back to another model's rates.

Catalog and pricing verified against Anthropic documentation on 2026-09-05.

---

## Project Context

Built as proof-of-work for Nature Heart AI Specialist application.

**Demonstrates:**
- Systematic AI evaluation methodology
- Prompt engineering discipline
- Cost/quality trade-off analysis
- Production-oriented code patterns
- Evidence-based development

**Does NOT claim:**
- Production deployment
- Live benchmark execution
- Multi-model comparison results
- Measured F1/precision/recall scores

---

## Author

Christopher Fliß  
Proof-of-Work for Nature Heart Application  
2026-09-04

---

## License

MIT License - See LICENSE file for details
