# Sentiment Analysis Engine

An advanced NLP sentiment analysis engine: BERT fine-tuning, data augmentation
for class balancing, a FastAPI inference service with ONNX acceleration, a
Gradio demo, and full Docker deployment.

## Architecture

```
                          +--------------------------+
                          |     Data Sources         |
                          |  SST-2 / Amazon / Twitter|
                          +-----------+--------------+
                                      |
                                      v
        +-----------------------------------------------------+
        |  src/data_pipeline.py                               |
        |  clean -> merge -> tokenize -> split (80/10/10)     |
        +-----------------------------+-----------------------+
                                      |
                                      v
        +-----------------------------------------------------+
        |  src/augmentation.py                                |
        |  synonym replace + back-translate minority classes  |
        +-----------------------------+-----------------------+
                                      |
                                      v
        +-----------------------------------------------------+
        |  src/trainer.py  (WeightedTrainer + compute_metrics)|
        |  src/model.py    (BERT + dropout + classifier)      |
        +-----------------------------+-----------------------+
                                      |
                          trained model + tokenizer
                                      |
                                      v
        +-----------------------------------------------------+
        |  src/inference.py  (ONNX Runtime / PyTorch)         |
        +-----------------------------+-----------------------+
                                      |
                +---------------------+---------------------+
                v                                           v
   +------------------------+                  +------------------------+
   |  api/main.py (FastAPI) |  <-- HTTP -->     |  app.py (Gradio demo)  |
   |  /predict /batch       |                  |  port 7860             |
   |  /health /metrics      |                  +------------------------+
   |  port 8000             |
   +------------------------+
```

## Quick start

```bash
git clone https://github.com/your-username/sentiment-engine.git
cd sentiment-engine
cp .env.example .env

# Option A: local
make install
make pipeline      # build datasets
make augment       # balance minority classes
make train         # fine-tune BERT
make serve         # start the API on :8000

# Option B: Docker (expects trained weights in ./models)
docker-compose up --build
# API  -> http://localhost:8000/docs
# Demo -> http://localhost:7860
```

## API documentation

| Endpoint | Method | Body | Response |
| --- | --- | --- | --- |
| `/predict` | POST | `{"text": "..."}` | `SentimentResult` (label, confidence, scores, processing_time_ms) |
| `/predict/batch` | POST | `{"texts": ["...", "..."]}` (max 64) | `{results: [...], total_time_ms}` |
| `/health` | GET | — | `{"status", "model", "device"}` |
| `/metrics` | GET | — | `{total_predictions, average_latency_ms, predictions_per_second, uptime_seconds}` |

Example:

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"text": "I absolutely love this!"}'
```

## Benchmarks

Targets (replace with measured values from `notebooks/evaluation.ipynb`):

| Metric | Value |
| --- | --- |
| Accuracy | 91% |
| Macro F1 | 0.90 |
| Latency p50 | < 60 ms |
| Latency p95 | < 200 ms |
| Latency p99 | < 250 ms |
| Throughput | 500+ samples/sec (batched, ONNX) |

## ONNX export (for throughput)

After training, export to ONNX so the inference engine uses ONNX Runtime:

```python
from pathlib import Path
from config import get_settings
from src.inference import SentimentInferenceEngine

settings = get_settings()
engine = SentimentInferenceEngine(settings.MODEL_DIR)        # PyTorch backend
engine.export_to_onnx(settings.MODEL_DIR / "model.onnx")     # opset 14
# Re-create the engine; it now auto-detects model.onnx and uses ONNX Runtime.
```

## Project layout

```
sentiment-engine/
├── config.py              # Pydantic settings (env-driven)
├── src/
│   ├── data_pipeline.py   # load, clean, tokenize, split
│   ├── augmentation.py    # synonym replace + back-translation
│   ├── model.py           # SentimentModel
│   ├── trainer.py         # WeightedTrainer + compute_metrics + train()
│   ├── inference.py       # SentimentInferenceEngine (ONNX/PyTorch)
│   └── logging_utils.py
├── api/
│   ├── main.py            # FastAPI app
│   └── schemas.py         # request/response models
├── tests/                 # pytest suite
├── notebooks/evaluation.ipynb
├── app.py                 # Gradio demo
├── Dockerfile             # multi-stage build
├── docker-compose.yml     # api + demo services
├── requirements.txt
├── Makefile
└── MODEL_CARD.md
```

## Testing

```bash
make test          # or: python -m pytest -v
```

## Live demo

Hosted on Hugging Face Spaces: https://huggingface.co/spaces/your-username/sentiment-engine

## License

MIT
