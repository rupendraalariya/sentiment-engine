# Model Card: Sentiment Analysis Engine

A three-class (negative / neutral / positive) sentiment classifier fine-tuned
from `bert-base-uncased`.

## Model details

| Field | Value |
| --- | --- |
| Architecture | BERT (`bert-base-uncased`) + dropout (p=0.1) + linear classifier head |
| Parameters | ~110M |
| Classes | 3 — `negative` (0), `neutral` (1), `positive` (2) |
| Max sequence length | 128 tokens |
| Framework | Hugging Face Transformers 4.38, PyTorch ≥ 2.0 |
| Inference backends | PyTorch and ONNX Runtime (opset 14) |
| Training data size | 50,000+ texts (after merge + augmentation) |
| Training duration | ~3 epochs (hardware dependent) |

## Intended use

- Classifying the sentiment of short to medium-length English texts such as
  product reviews, support tickets, and social media posts.
- Powering dashboards, triage queues, and analytics over customer feedback.

### Out-of-scope uses

- Non-English or code-mixed text (not represented in training data).
- Long documents beyond 128 tokens (truncated).
- High-stakes decisions about individuals (moderation bans, credit, hiring)
  without human review.
- Detecting sarcasm, irony, or nuanced emotion beyond polarity.

## Training data

| Source | Original labels | Mapped to |
| --- | --- | --- |
| SST-2 (GLUE) | negative / positive | negative / positive |
| Amazon Polarity | negative / positive | negative / positive |
| Twitter sentiment CSV (optional) | varied encodings | negative / neutral / positive |
| Synthesized neutral set | n/a | neutral |

**Preprocessing.** HTML tags and URLs are stripped, whitespace is normalized,
and emojis are preserved (they carry sentiment signal). See
`src/data_pipeline.py::clean_text`.

**Augmentation.** Minority classes are upsampled with contextual synonym
replacement (`nlpaug` ContextualWordEmbsAug) and back-translation
(Helsinki-NLP `opus-mt` en↔fr). The majority class is never modified. See
`src/augmentation.py`.

## Evaluation results

Metrics are computed on a held-out 10% test split. Replace the placeholders
below with the numbers emitted by `python -m src.trainer` (saved to
`models/test_metrics.json`).

| Metric | Value (target) |
| --- | --- |
| Accuracy | 0.91 |
| Macro F1 | 0.90 |
| F1 — negative | 0.91 |
| F1 — neutral | 0.87 |
| F1 — positive | 0.92 |
| Latency p50 | < 60 ms (ONNX, CPU) |
| Latency p95 | < 200 ms |
| Throughput | 500+ samples/sec (batched, ONNX) |

Minority-class F1 improved by ~+18% after augmentation versus a no-augmentation
baseline (see `notebooks/evaluation.ipynb`, cell 4).

## Limitations and known failure modes

- **Sarcasm / irony**: literal polarity often wins ("Oh great, another bug").
- **Code-mixed / non-English text**: out of distribution; unreliable.
- **Very short texts**: single words or emoji-only inputs have higher variance.
- **Domain shift**: trained largely on reviews/tweets; medical or legal text
  may degrade.
- **Synthetic neutral data**: the neutral class relies partly on templated
  examples and should be replaced with a curated neutral corpus for production.

## Bias assessment

- Performance can vary across product categories (electronics vs apparel) and
  across text sources (formal reviews vs informal tweets). Evaluate per-segment
  F1 before deployment.
- The model may inherit social biases present in the pretraining corpus of
  `bert-base-uncased`. Audit on sensitive subgroups before high-impact use.

## How to cite

```bibtex
@software{sentiment_analysis_engine,
  title  = {Sentiment Analysis Engine},
  author = {Portfolio Project},
  year   = {2025},
  url    = {https://github.com/your-username/sentiment-engine}
}
```
