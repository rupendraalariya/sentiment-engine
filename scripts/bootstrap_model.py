"""Create an initial (untrained) model so the API can serve immediately.

This downloads ``bert-base-uncased`` and saves a 3-class classification head +
tokenizer into ``MODEL_DIR``. The classifier is randomly initialized, so
predictions are not meaningful until you run ``python -m src.trainer`` to
fine-tune. This exists purely to make the local server runnable end-to-end.

Usage::

    python -m scripts.bootstrap_model
"""

from __future__ import annotations

import os

from config import get_settings
from src.logging_utils import get_logger
from src.model import SentimentModel

logger = get_logger(__name__)


def main() -> None:
    """Build and persist a fresh SentimentModel to ``MODEL_DIR``.

    Set ``BOOTSTRAP_PRETRAINED=1`` to download the full pretrained backbone.
    By default the model is built from config only (random init) so the server
    is runnable without a large weight download.
    """
    settings = get_settings()
    settings.ensure_dirs()
    pretrained = os.environ.get("BOOTSTRAP_PRETRAINED", "0") == "1"
    logger.info(
        "Building bootstrap model from %s (pretrained=%s) ...",
        settings.MODEL_NAME,
        pretrained,
    )
    model = SentimentModel(
        model_name=settings.MODEL_NAME,
        num_labels=settings.NUM_LABELS,
        pretrained=pretrained,
    )
    model.save(settings.MODEL_DIR)
    logger.info(
        "Bootstrap model saved to %s. NOTE: classifier head is untrained; "
        "run `python -m src.trainer` to fine-tune.",
        settings.MODEL_DIR,
    )


if __name__ == "__main__":  # pragma: no cover
    main()
