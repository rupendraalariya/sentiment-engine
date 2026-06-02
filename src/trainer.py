"""Training pipeline for the NLP Sentiment Analysis Engine.

Provides:

* :func:`compute_metrics` - rich evaluation metrics for the Trainer.
* :class:`WeightedTrainer` - a :class:`~transformers.Trainer` subclass that
  applies class weights in the loss to combat class imbalance.
* :func:`train` - the end-to-end fine-tuning entry point.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import torch
from torch import nn

from config import ID2LABEL, Settings, get_settings
from src.logging_utils import get_logger

logger = get_logger(__name__)

_CLASS_ORDER = [ID2LABEL[i] for i in sorted(ID2LABEL)]  # [negative, neutral, positive]


def compute_metrics(eval_pred: Any) -> dict:
    """Compute classification metrics for the Trainer.

    Parameters
    ----------
    eval_pred:
        A tuple-like ``(predictions, label_ids)`` as produced by the Trainer.
        ``predictions`` may be logits of shape ``(N, num_labels)``.

    Returns
    -------
    dict
        Dictionary with ``accuracy``, ``macro_f1``, ``weighted_f1``,
        ``per_class_f1`` (keyed by class name) and a JSON-serializable
        ``confusion_matrix`` (nested list).
    """
    from sklearn.metrics import (
        accuracy_score,
        confusion_matrix,
        f1_score,
    )

    predictions, labels = eval_pred
    predictions = np.asarray(predictions)
    if predictions.ndim > 1:
        preds = predictions.argmax(axis=-1)
    else:
        preds = predictions
    labels = np.asarray(labels)

    num_labels = len(ID2LABEL)
    label_range = list(range(num_labels))

    accuracy = float(accuracy_score(labels, preds))
    macro_f1 = float(f1_score(labels, preds, average="macro", labels=label_range, zero_division=0))
    weighted_f1 = float(
        f1_score(labels, preds, average="weighted", labels=label_range, zero_division=0)
    )
    per_class = f1_score(
        labels, preds, average=None, labels=label_range, zero_division=0
    )
    per_class_f1 = {
        ID2LABEL[i]: float(per_class[i]) for i in range(num_labels)
    }
    cm = confusion_matrix(labels, preds, labels=label_range).tolist()

    return {
        "accuracy": accuracy,
        "macro_f1": macro_f1,
        "weighted_f1": weighted_f1,
        "per_class_f1": per_class_f1,
        "confusion_matrix": cm,
    }


class WeightedTrainer:
    """Mixin-style factory producing a class-weighted ``Trainer`` subclass.

    The actual ``transformers.Trainer`` is imported lazily inside
    :func:`build_weighted_trainer` so that importing this module (e.g. for unit
    testing :func:`compute_metrics`) does not require the full training stack.

    Use :func:`build_weighted_trainer` to construct a concrete instance.
    """


def build_weighted_trainer(
    class_weights: torch.Tensor | None,
    **trainer_kwargs: Any,
):
    """Build a :class:`~transformers.Trainer` that applies class weights.

    Parameters
    ----------
    class_weights:
        A 1-D tensor of per-class weights, or ``None`` for unweighted loss.
    **trainer_kwargs:
        Forwarded verbatim to the ``Trainer`` constructor.

    Returns
    -------
    transformers.Trainer
        A configured trainer instance with a weighted cross-entropy loss.
    """
    from transformers import Trainer

    class _WeightedTrainer(Trainer):
        """``Trainer`` that overrides :meth:`compute_loss` with class weights."""

        def __init__(self, *args: Any, weights: torch.Tensor | None = None, **kwargs: Any) -> None:
            super().__init__(*args, **kwargs)
            self._class_weights = weights

        def compute_loss(  # type: ignore[override]
            self,
            model: nn.Module,
            inputs: dict,
            return_outputs: bool = False,
            **kwargs: Any,
        ):
            """Weighted cross-entropy loss over the model logits."""
            labels = inputs.pop("labels")
            outputs = model(**inputs)
            logits = outputs.logits if hasattr(outputs, "logits") else outputs[0]

            weight = None
            if self._class_weights is not None:
                weight = self._class_weights.to(logits.device)
            loss_fct = nn.CrossEntropyLoss(weight=weight)
            loss = loss_fct(
                logits.view(-1, logits.size(-1)), labels.view(-1)
            )
            return (loss, outputs) if return_outputs else loss

    return _WeightedTrainer(weights=class_weights, **trainer_kwargs)


def _tokenizer_kwarg(tokenizer: Any) -> dict:
    """Return the correct Trainer kwarg for the tokenizer across versions.

    Transformers 5.x replaced the ``tokenizer`` argument with
    ``processing_class``. This helper picks whichever the installed Trainer
    supports.
    """
    import inspect

    from transformers import Trainer

    params = set(inspect.signature(Trainer.__init__).parameters)
    if "processing_class" in params:
        return {"processing_class": tokenizer}
    return {"tokenizer": tokenizer}


def _build_training_arguments(training_arguments_cls: Any, config: Settings) -> Any:
    """Construct ``TrainingArguments`` robustly across transformers versions.

    Transformers 5.x renamed ``evaluation_strategy`` to ``eval_strategy`` and
    dropped the ``tokenizer`` Trainer argument in favor of ``processing_class``.
    This helper inspects the available constructor parameters and only passes
    keys that are supported, so the pipeline works on both 4.38.x and 5.x.

    Parameters
    ----------
    training_arguments_cls:
        The ``transformers.TrainingArguments`` class.
    config:
        Project settings.

    Returns
    -------
    transformers.TrainingArguments
        A configured instance.
    """
    import inspect

    supported = set(inspect.signature(training_arguments_cls.__init__).parameters)

    kwargs: dict[str, Any] = {
        "output_dir": str(config.MODEL_DIR),
        "num_train_epochs": config.NUM_EPOCHS,
        "per_device_train_batch_size": config.BATCH_SIZE,
        "per_device_eval_batch_size": config.BATCH_SIZE,
        "learning_rate": config.LEARNING_RATE,
        "warmup_steps": config.WARMUP_STEPS,
        "weight_decay": config.WEIGHT_DECAY,
        "save_strategy": "epoch",
        "load_best_model_at_end": True,
        "metric_for_best_model": "eval_macro_f1",
        "greater_is_better": True,
        "logging_dir": str(config.MODEL_DIR / "logs"),
        "logging_steps": 50,
        "report_to": [config.REPORT_TO] if config.REPORT_TO != "none" else [],
        "run_name": config.WANDB_PROJECT,
    }

    # Evaluation-strategy key differs by version.
    if "eval_strategy" in supported:
        kwargs["eval_strategy"] = "epoch"
    elif "evaluation_strategy" in supported:
        kwargs["evaluation_strategy"] = "epoch"

    # Drop any unsupported keys defensively.
    kwargs = {k: v for k, v in kwargs.items() if k in supported}
    return training_arguments_cls(**kwargs)


def train(config: Settings | None = None) -> dict:
    """Run the full fine-tuning pipeline.

    Steps
    -----
    1. Load the augmented train split and the validation/test splits from disk.
    2. Tokenize all splits.
    3. Build a :class:`SentimentModel` and a class-weighted trainer.
    4. Train, evaluate on the held-out test set, and save the best model.
    5. Print a full classification report.

    Parameters
    ----------
    config:
        Optional settings object. Defaults to :func:`config.get_settings`.

    Returns
    -------
    dict
        The test-set metrics returned by :func:`compute_metrics`.
    """
    from datasets import load_from_disk
    from sklearn.metrics import classification_report
    from transformers import TrainingArguments

    from src.data_pipeline import get_class_weights, tokenize_dataset
    from src.model import SentimentModel

    config = config or get_settings()
    config.ensure_dirs()

    # ---- Load data ----
    processed = load_from_disk(str(config.PROCESSED_DIR))
    if config.AUGMENTED_DIR.exists():
        logger.info("Loading augmented training split from %s", config.AUGMENTED_DIR)
        train_ds = load_from_disk(str(config.AUGMENTED_DIR))
    else:
        logger.warning(
            "Augmented dataset not found; falling back to processed train split."
        )
        train_ds = processed["train"]
    val_ds = processed["validation"]
    test_ds = processed["test"]

    # ---- Model + tokenizer ----
    model = SentimentModel(
        model_name=config.MODEL_NAME, num_labels=config.NUM_LABELS
    )
    tokenizer = model.tokenizer

    # ---- Tokenize ----
    train_tok = tokenize_dataset(train_ds, tokenizer, config.MAX_LENGTH)
    val_tok = tokenize_dataset(val_ds, tokenizer, config.MAX_LENGTH)
    test_tok = tokenize_dataset(test_ds, tokenizer, config.MAX_LENGTH)

    class_weights = get_class_weights(train_tok, config.NUM_LABELS)

    # ---- Training arguments ----
    args = _build_training_arguments(TrainingArguments, config)

    trainer = build_weighted_trainer(
        class_weights=class_weights,
        model=model,
        args=args,
        train_dataset=train_tok,
        eval_dataset=val_tok,
        compute_metrics=compute_metrics,
        **_tokenizer_kwarg(tokenizer),
    )

    # ---- Train ----
    logger.info("Starting training ...")
    trainer.train()

    # ---- Evaluate on test set ----
    logger.info("Evaluating on the held-out test set ...")
    predictions = trainer.predict(test_tok)
    test_metrics = compute_metrics((predictions.predictions, predictions.label_ids))

    preds = np.asarray(predictions.predictions).argmax(axis=-1)
    report = classification_report(
        predictions.label_ids,
        preds,
        labels=list(range(config.NUM_LABELS)),
        target_names=_CLASS_ORDER,
        zero_division=0,
    )
    logger.info("Classification report:\n%s", report)

    # ---- Persist final model + metrics ----
    model.save(config.MODEL_DIR)
    metrics_path = config.MODEL_DIR / "test_metrics.json"
    metrics_path.write_text(json.dumps(test_metrics, indent=2), encoding="utf-8")
    logger.info("Saved test metrics to %s", metrics_path)

    return test_metrics


if __name__ == "__main__":  # pragma: no cover
    train()
