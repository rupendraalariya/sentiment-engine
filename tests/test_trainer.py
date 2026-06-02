"""Unit tests for :mod:`src.trainer`.

These tests focus on :func:`compute_metrics`, which can be validated with
plain NumPy arrays and does not require the full training stack.
"""

from __future__ import annotations

import numpy as np

from src.trainer import compute_metrics


class TestComputeMetrics:
    """Tests for the custom ``compute_metrics`` function."""

    def _make_eval_pred(self):
        """Build a small logits/labels pair covering all three classes."""
        # 6 samples, 3 classes. Logits as argmax-able rows.
        logits = np.array(
            [
                [3.0, 0.1, 0.1],  # -> 0 negative
                [0.1, 3.0, 0.1],  # -> 1 neutral
                [0.1, 0.1, 3.0],  # -> 2 positive
                [3.0, 0.1, 0.1],  # -> 0 negative
                [0.1, 0.1, 3.0],  # -> 2 positive
                [0.1, 3.0, 0.1],  # -> 1 neutral
            ]
        )
        labels = np.array([0, 1, 2, 0, 2, 1])
        return logits, labels

    def test_returns_all_expected_keys(self) -> None:
        """All required metric keys are present."""
        metrics = compute_metrics(self._make_eval_pred())
        for key in (
            "accuracy",
            "macro_f1",
            "weighted_f1",
            "per_class_f1",
            "confusion_matrix",
        ):
            assert key in metrics

    def test_per_class_f1_keys(self) -> None:
        """``per_class_f1`` is keyed by the three class names."""
        metrics = compute_metrics(self._make_eval_pred())
        assert set(metrics["per_class_f1"].keys()) == {
            "negative",
            "neutral",
            "positive",
        }

    def test_perfect_predictions_score_one(self) -> None:
        """A perfectly classified batch yields accuracy and F1 of 1.0."""
        metrics = compute_metrics(self._make_eval_pred())
        assert metrics["accuracy"] == 1.0
        assert metrics["macro_f1"] == 1.0
        assert metrics["weighted_f1"] == 1.0

    def test_confusion_matrix_is_json_serializable(self) -> None:
        """The confusion matrix is a nested list (JSON-serializable)."""
        import json

        metrics = compute_metrics(self._make_eval_pred())
        cm = metrics["confusion_matrix"]
        assert isinstance(cm, list)
        assert all(isinstance(row, list) for row in cm)
        # Should not raise.
        json.dumps(cm)
        # 3x3 for three classes.
        assert len(cm) == 3
        assert all(len(row) == 3 for row in cm)

    def test_handles_imperfect_predictions(self) -> None:
        """Metrics degrade gracefully with some wrong predictions."""
        logits = np.array(
            [
                [3.0, 0.1, 0.1],  # pred 0, true 0  ok
                [3.0, 0.1, 0.1],  # pred 0, true 1  wrong
                [0.1, 0.1, 3.0],  # pred 2, true 2  ok
            ]
        )
        labels = np.array([0, 1, 2])
        metrics = compute_metrics((logits, labels))
        assert 0.0 <= metrics["accuracy"] <= 1.0
        assert abs(metrics["accuracy"] - (2 / 3)) < 1e-6
