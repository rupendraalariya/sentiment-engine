"""Unit tests for :mod:`src.data_pipeline`."""

from __future__ import annotations

import torch
from datasets import Dataset

from src.data_pipeline import clean_text, get_class_weights, split_and_save


class TestCleanText:
    """Edge-case coverage for :func:`clean_text`."""

    def test_strips_html_tags(self) -> None:
        """HTML tags are removed but inner text is preserved."""
        assert clean_text("<p>Great <b>product</b>!</p>") == "Great product !"

    def test_strips_urls(self) -> None:
        """URLs (http and www) are removed."""
        result = clean_text("Check this http://example.com and www.test.org now")
        assert "http" not in result
        assert "www.test.org" not in result
        assert "Check this" in result

    def test_preserves_emoji(self) -> None:
        """Emojis carry sentiment signal and must be kept."""
        result = clean_text("I love this 😍🔥")
        assert "😍" in result
        assert "🔥" in result

    def test_empty_string(self) -> None:
        """Empty input returns an empty string."""
        assert clean_text("") == ""

    def test_non_string_input(self) -> None:
        """Non-string input is coerced safely to an empty string."""
        assert clean_text(None) == ""  # type: ignore[arg-type]

    def test_very_long_text_normalizes_whitespace(self) -> None:
        """Long text with messy whitespace collapses to single spaces."""
        raw = ("word   \n\t " * 1000).strip()
        result = clean_text(raw)
        assert "  " not in result
        assert "\n" not in result
        assert "\t" not in result
        assert result.startswith("word")


class TestGetClassWeights:
    """Tests for inverse-frequency class weighting."""

    def test_balanced_dataset_has_equal_weights(self) -> None:
        """A perfectly balanced dataset yields equal weights of 1.0."""
        ds = Dataset.from_dict({"label": [0, 1, 2, 0, 1, 2]})
        weights = get_class_weights(ds, num_labels=3)
        assert isinstance(weights, torch.Tensor)
        assert torch.allclose(weights, torch.ones(3), atol=1e-6)

    def test_minority_class_gets_higher_weight(self) -> None:
        """The rarest class receives the largest weight."""
        ds = Dataset.from_dict({"label": [0, 0, 0, 0, 1, 2, 2]})
        weights = get_class_weights(ds, num_labels=3)
        # Class 1 has a single sample -> highest weight.
        assert weights[1] > weights[0]
        assert weights[1] > weights[2]

    def test_missing_class_gets_zero_weight(self) -> None:
        """A class with no samples receives a weight of 0."""
        ds = Dataset.from_dict({"label": [0, 0, 2, 2]})
        weights = get_class_weights(ds, num_labels=3)
        assert weights[1].item() == 0.0


class TestSplitAndSave:
    """Tests for the 80/10/10 split + persistence helper."""

    def test_split_ratios_and_persistence(self, tmp_path) -> None:
        """Splits roughly match 80/10/10 and are written to disk."""
        ds = Dataset.from_dict(
            {"text": [f"sample {i}" for i in range(100)], "label": [i % 3 for i in range(100)]}
        )
        splits = split_and_save(ds, tmp_path / "processed")
        assert len(splits["train"]) == 80
        assert len(splits["validation"]) == 10
        assert len(splits["test"]) == 10
        # Arrow artifacts exist on disk.
        assert (tmp_path / "processed").exists()
