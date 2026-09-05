# Why This Project Exists — Job Responsibility Match

## The Nature Heart Role Says:

> **"Evaluierung neuer AI-Funktionen und Modelle sowie Erstellung von Empfehlungen"**

Translation: *Evaluate new AI features and models, provide recommendations*

## The Problem:

How do you systematically compare AI models/tools?

Most teams evaluate AI by:
- ❌ Vibes and demos
- ❌ Vendor marketing claims
- ❌ Anecdotal testing
- ❌ No cost/quality trade-off analysis

## What This Harness Shows:

✅ **Systematic Comparison Framework**
- Multiple prompt strategies tested side-by-side
- Quantitative metrics: Precision, Recall, F1, Latency, Cost
- Golden test set (30 cases) prevents cherry-picking
- Regression tests prevent prompt degradation

✅ **Cost-Aware Evaluation**
- Token counting per request
- Cost per 1K classifications
- Latency tracking
- Trade-off analysis (fast/cheap vs. accurate/expensive)

✅ **Production Thinking**
- Audit trail (JSONL format)
- Confidence scoring (0.0-1.0)
- Human escalation logic
- Evidence extraction
- Reproducible results

## How It Would Be Used at Nature Heart:

**Scenario:** "Should we use Haiku, Sonnet, or Opus for [task]?"

**Process:**
1. Define golden test set (30 representative cases)
2. Create 3 prompt variants (direct, chain-of-thought, few-shot)
3. Run each model on each variant
4. Compare: Accuracy × Latency × Cost
5. Recommendation, stated in the shape the data supports: which variant wins on
   F1, what that costs per 1K classifications, and where the human gate sits

**Output:** measured numbers rather than opinions — once the run is authorised.
No benchmark figures appear anywhere in this repository, because none were measured.

## Transferability:

This framework isn't content-moderation-specific.

The same infrastructure evaluates:
- Health claims compliance checking
- Creator content quality scoring
- Customer support classification
- Any AI task requiring systematic evaluation

## What I'm NOT Claiming:

❌ I know what models Nature Heart uses  
❌ I know what evaluation criteria Nature Heart needs  
❌ This is the "right" framework for every use case  

✅ I can build systematic evaluation tools  
✅ I understand cost/quality trade-offs  
✅ I think in evidence and metrics, not vibes  

## Connection to Application:

The job asks for someone who can:
- Evaluate AI features/models
- Provide recommendations
- Use Anthropic API
- Do prompt engineering
- Think systematically

This project demonstrates all five.

**Not described. Shown.**

---

**Related Files:**
- `README.md` — Setup & usage
- `docs/case-study.md` — Architecture deep-dive
- `docs/test-report.md` — Sample evaluation results
- `src/prompt_bench.py` — Comparison CLI
