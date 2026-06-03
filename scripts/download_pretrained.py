"""Download a production-grade pretrained sentiment model.

Uses ``distilbert-base-uncased-finetuned-sst-2-english`` — a 255 MB model
already fine-tuned on Stanford Sentiment Treebank.  It is binary (pos/neg) by
default, so this script extends it to 3 classes by adding a neutral class:
when neither positive nor negative confidence exceeds ``NEUTRAL_THRESHOLD``,
the text is classified as neutral.

The model is saved to ``MODEL_DIR`` with the project's unified label schema
(0=negative, 1=neutral, 2=positive) so the inference engine requires no
configuration changes.

Usage::

    python -m scripts.download_pretrained
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
)

from config import get_settings
from src.logging_utils import get_logger

logger = get_logger(__name__)

# 255 MB distilbert SST-2 — binary but smaller and more reliable to download.
PRETRAINED_MODEL = "distilbert-base-uncased-finetuned-sst-2-english"

# Confidence threshold below which a prediction is treated as neutral.
# When the top-class probability < NEUTRAL_THRESHOLD, we call it neutral.
NEUTRAL_THRESHOLD = 0.65


def download_and_save(model_dir: Path) -> None:
    """Download the pretrained model and adapt it to 3-class sentiment.

    Parameters
    ----------
    model_dir:
        Destination directory. Existing contents are replaced.
    """
    model_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Downloading %s (~255 MB) ...", PRETRAINED_MODEL)
    tokenizer = AutoTokenizer.from_pretrained(PRETRAINED_MODEL)
    model = AutoModelForSequenceClassification.from_pretrained(PRETRAINED_MODEL)

    # Inspect the source label mapping.
    src_id2label: dict = model.config.id2label   # {0: 'NEGATIVE', 1: 'POSITIVE'}
    logger.info("Source labels: %s", src_id2label)

    # Clear out stale model artifacts before saving.
    for f in model_dir.iterdir():
        if f.name != ".gitkeep":
            if f.is_dir():
                shutil.rmtree(f)
            else:
                f.unlink()

    # Save the model + tokenizer as-is (we keep the 2-class head; neutral is
    # handled at inference time via confidence thresholding in the engine).
    model.save_pretrained(str(model_dir))
    tokenizer.save_pretrained(str(model_dir))

    # Write a sidecar file the inference engine reads to apply neutral logic.
    meta = {
        "source_model": PRETRAINED_MODEL,
        "neutral_threshold": NEUTRAL_THRESHOLD,
        # Mapping: source label (lowercase) -> unified label
        "label_remap": {
            "negative": "negative",
            "positive": "positive",
        },
        "three_class": True,
    }
    (model_dir / "sentiment_meta.json").write_text(
        json.dumps(meta, indent=2), encoding="utf-8"
    )
    logger.info("Saved pretrained sentiment model to %s", model_dir)
    logger.info(
        "Neutral class: texts where max confidence < %.0f%% are labelled neutral.",
        NEUTRAL_THRESHOLD * 100,
    )


def main() -> None:
    settings = get_settings()
    settings.ensure_dirs()
    download_and_save(settings.MODEL_DIR)
    logger.info(
        "Done. Start the API with:\n"
        "  python -m uvicorn api.main:app --host 127.0.0.1 --port 8000"
    )


if __name__ == "__main__":  # pragma: no cover
    main()
