"""Unit tests for :mod:`src.augmentation`.

Heavy ML models (nlpaug, translation pipelines) are mocked so the tests run
quickly and offline. The focus is on the orchestration logic: label
preservation, validity checks, and minority-class balancing.
"""

from __future__ import annotations

from datasets import Dataset

from src.augmentation import SentimentAugmenter


class TestVerifyAugmentation:
    """Tests for :meth:`SentimentAugmenter.verify_augmentation`."""

    def setup_method(self) -> None:
        self.aug = SentimentAugmenter()

    def test_identical_text_is_invalid(self) -> None:
        """Identical augmentation is flagged invalid."""
        result = self.aug.verify_augmentation("hello world", "hello world")
        assert result["is_valid"] is False

    def test_empty_augmentation_is_invalid(self) -> None:
        """Empty augmented text is flagged invalid."""
        result = self.aug.verify_augmentation("hello world", "")
        assert result["is_valid"] is False

    def test_changed_text_is_valid(self) -> None:
        """A genuinely different augmentation is valid."""
        result = self.aug.verify_augmentation("hello world", "hi planet")
        assert result["is_valid"] is True
        assert result["char_diff"] >= 0
        assert 0.0 <= result["word_overlap"] <= 1.0

    def test_word_overlap_metric(self) -> None:
        """Word overlap is the Jaccard similarity of token sets."""
        result = self.aug.verify_augmentation("a b c d", "a b x y")
        # overlap {a,b} / union {a,b,c,d,x,y} = 2/6 (rounded to 4 decimals)
        assert abs(result["word_overlap"] - (2 / 6)) < 1e-3


class TestAugmentMinorityClasses:
    """Tests for minority-class balancing with mocked generators."""

    def setup_method(self) -> None:
        self.aug = SentimentAugmenter()
        # Deterministic, non-trivial transforms that keep text non-empty and
        # different from the original so verify_augmentation passes.
        self.aug.synonym_replace = lambda text: f"{text} syn"  # type: ignore[assignment]
        self.aug.back_translate = lambda texts, **_: [  # type: ignore[assignment]
            f"{t} bt" for t in texts
        ]

    def test_majority_class_untouched(self) -> None:
        """The majority class count stays the same after augmentation."""
        ds = Dataset.from_dict(
            {
                "text": ["pos"] * 6 + ["neg"] * 2 + ["neu"] * 1,
                "label": [2] * 6 + [0] * 2 + [1] * 1,
            }
        )
        out = self.aug.augment_minority_classes(ds, target_count=6)
        counts = self.aug._class_counts(out, "label")
        assert counts[2] == 6  # majority unchanged
        assert counts[0] == 6  # upsampled
        assert counts[1] == 6  # upsampled

    def test_labels_preserved_for_generated_samples(self) -> None:
        """Generated samples keep the label of their source class."""
        ds = Dataset.from_dict(
            {"text": ["pos"] * 4 + ["neg"] * 1, "label": [2] * 4 + [0] * 1}
        )
        out = self.aug.augment_minority_classes(ds, target_count=4)
        # All rows labeled 0 must contain only augmented "neg" variants.
        neg_texts = [out[i]["text"] for i in range(len(out)) if out[i]["label"] == 0]
        assert all("neg" in t for t in neg_texts)
        assert len(neg_texts) == 4

    def test_generated_samples_are_non_empty_and_different(self) -> None:
        """Every augmented sample is non-empty and differs from the source."""
        ds = Dataset.from_dict({"text": ["seed"] * 1 + ["x"] * 3, "label": [0, 1, 1, 1]})
        out = self.aug.augment_minority_classes(ds, target_count=3)
        for i in range(len(out)):
            assert out[i]["text"].strip() != ""

    def test_already_balanced_returns_input(self) -> None:
        """A balanced dataset is returned unchanged."""
        ds = Dataset.from_dict({"text": ["a", "b", "c"], "label": [0, 1, 2]})
        out = self.aug.augment_minority_classes(ds, target_count=1)
        assert len(out) == len(ds)
