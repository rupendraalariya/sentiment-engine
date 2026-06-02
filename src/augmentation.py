"""Data augmentation for the NLP Sentiment Analysis Engine.

Implements :class:`SentimentAugmenter`, which balances minority sentiment
classes using two complementary techniques:

* **Contextual synonym replacement** via ``nlpaug``'s
  :class:`ContextualWordEmbsAug` (BERT embeddings).
* **Back-translation** (English -> French -> English) using Helsinki-NLP
  ``opus-mt`` models.

Augmentation is applied *only* to classes below a target count so the majority
class is never touched, preserving the label semantics throughout.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from datasets import Dataset, concatenate_datasets

from config import ID2LABEL, get_settings
from src.logging_utils import get_logger

if TYPE_CHECKING:  # pragma: no cover - typing only
    pass

logger = get_logger(__name__)

_BACK_TRANSLATE_BATCH = 32


class SentimentAugmenter:
    """Augment minority sentiment classes while preserving labels.

    Parameters
    ----------
    aug_percent:
        Fraction of non-stopword tokens to replace during synonym replacement.
    device:
        Torch device string (``"cpu"`` or ``"cuda"``) used by the underlying
        models.
    model_name:
        Embedding model used for contextual synonym replacement.

    Notes
    -----
    The heavy ``nlpaug`` and translation models are loaded lazily on first use
    so importing this module (e.g. during tests) stays cheap.
    """

    def __init__(
        self,
        aug_percent: float = 0.15,
        device: str = "cpu",
        model_name: str = "bert-base-uncased",
    ) -> None:
        self.aug_percent = aug_percent
        self.device = device
        self.model_name = model_name
        self._syn_aug = None  # lazily initialized nlpaug augmenter
        self._mt_pipelines: dict[str, object] = {}

    # ------------------------------------------------------------------ #
    # Synonym replacement
    # ------------------------------------------------------------------ #
    def _get_synonym_aug(self):
        """Lazily build the contextual word-embeddings augmenter."""
        if self._syn_aug is None:
            import nlpaug.augmenter.word as naw

            logger.info(
                "Initializing ContextualWordEmbsAug (%s) on %s",
                self.model_name,
                self.device,
            )
            self._syn_aug = naw.ContextualWordEmbsAug(
                model_path=self.model_name,
                action="substitute",
                aug_p=self.aug_percent,
                device=self.device,
            )
        return self._syn_aug

    def synonym_replace(self, text: str) -> str:
        """Replace a fraction of tokens with contextual synonyms.

        Parameters
        ----------
        text:
            Input text to augment.

        Returns
        -------
        str
            The augmented text, or the original text if augmentation fails or
            produces an empty result.
        """
        if not text or not text.strip():
            return text
        try:
            aug = self._get_synonym_aug()
            result = aug.augment(text)
            # nlpaug returns a list for a single string in recent versions.
            augmented = result[0] if isinstance(result, list) else result
            return augmented if augmented and augmented.strip() else text
        except Exception as exc:  # noqa: BLE001 - resilient augmentation
            logger.warning("Synonym replacement failed: %s", exc)
            return text

    # ------------------------------------------------------------------ #
    # Back-translation
    # ------------------------------------------------------------------ #
    def _get_translation_pipeline(self, src: str, tgt: str):
        """Lazily build (and cache) a translation pipeline for ``src->tgt``."""
        key = f"{src}-{tgt}"
        if key not in self._mt_pipelines:
            from transformers import pipeline

            model = f"Helsinki-NLP/opus-mt-{src}-{tgt}"
            logger.info("Loading translation model %s", model)
            device_id = 0 if self.device.startswith("cuda") else -1
            self._mt_pipelines[key] = pipeline(
                "translation",
                model=model,
                device=device_id,
            )
        return self._mt_pipelines[key]

    def back_translate(
        self,
        texts: list[str],
        src_lang: str = "en",
        pivot_lang: str = "fr",
    ) -> list[str]:
        """Back-translate texts through a pivot language for paraphrasing.

        Each text is translated ``src_lang -> pivot_lang -> src_lang`` in
        batches for efficiency.

        Parameters
        ----------
        texts:
            List of input texts.
        src_lang:
            Source (and final) language code.
        pivot_lang:
            Intermediate pivot language code.

        Returns
        -------
        list[str]
            Back-translated texts. On failure the original text is returned for
            that element, so the output length always matches the input.
        """
        if not texts:
            return []
        try:
            forward = self._get_translation_pipeline(src_lang, pivot_lang)
            backward = self._get_translation_pipeline(pivot_lang, src_lang)

            pivoted = self._run_translation(forward, texts)
            result = self._run_translation(backward, pivoted)
            # Guard against length mismatches.
            return [
                res if res and res.strip() else original
                for res, original in zip(result, texts)
            ]
        except Exception as exc:  # noqa: BLE001 - resilient augmentation
            logger.warning("Back-translation failed: %s", exc)
            return list(texts)

    @staticmethod
    def _run_translation(translator, texts: list[str]) -> list[str]:
        """Run a translation pipeline over texts in fixed-size batches."""
        outputs: list[str] = []
        for start in range(0, len(texts), _BACK_TRANSLATE_BATCH):
            batch = texts[start : start + _BACK_TRANSLATE_BATCH]
            translated = translator(batch)
            outputs.extend(item["translation_text"] for item in translated)
        return outputs

    # ------------------------------------------------------------------ #
    # Verification
    # ------------------------------------------------------------------ #
    def verify_augmentation(self, original: str, augmented: str) -> dict:
        """Measure how much an augmentation changed the text.

        Parameters
        ----------
        original:
            The original text.
        augmented:
            The augmented text.

        Returns
        -------
        dict
            ``{'char_diff': int, 'word_overlap': float, 'is_valid': bool}``.
            ``is_valid`` is ``False`` when the augmented text is empty or
            identical to the original.
        """
        char_diff = abs(len(augmented) - len(original))
        orig_words = set(original.lower().split())
        aug_words = set(augmented.lower().split())
        union = orig_words | aug_words
        word_overlap = len(orig_words & aug_words) / len(union) if union else 0.0

        is_valid = bool(augmented.strip()) and augmented.strip() != original.strip()

        return {
            "char_diff": char_diff,
            "word_overlap": round(word_overlap, 4),
            "is_valid": is_valid,
        }

    # ------------------------------------------------------------------ #
    # Minority-class balancing
    # ------------------------------------------------------------------ #
    def augment_minority_classes(
        self,
        dataset: Dataset,
        target_count: int,
    ) -> Dataset:
        """Balance the dataset by augmenting classes below ``target_count``.

        For every class with fewer than ``target_count`` samples, new samples
        are generated by combining synonym replacement and back-translation of
        existing samples of that class until the target is reached. The majority
        class(es) are never modified.

        Parameters
        ----------
        dataset:
            Dataset with ``text`` and ``label`` columns.
        target_count:
            Desired minimum number of samples per class.

        Returns
        -------
        Dataset
            The original dataset concatenated with the generated samples,
            shuffled.
        """
        label_col = "labels" if "labels" in dataset.column_names else "label"
        counts = self._class_counts(dataset, label_col)
        logger.info(
            "Class counts before augmentation: %s",
            {ID2LABEL.get(k, k): v for k, v in counts.items()},
        )

        generated_texts: list[str] = []
        generated_labels: list[int] = []

        for label, count in counts.items():
            if count >= target_count:
                continue
            needed = target_count - count
            source_texts = [
                dataset[i]["text"]
                for i in range(len(dataset))
                if int(dataset[i][label_col]) == label
            ]
            if not source_texts:
                logger.warning("No source texts for class %s - skipping.", label)
                continue

            new_texts = self._generate_samples(source_texts, needed)
            generated_texts.extend(new_texts)
            generated_labels.extend([label] * len(new_texts))
            logger.info(
                "Class %s: +%d samples (target %d).",
                ID2LABEL.get(label, label),
                len(new_texts),
                target_count,
            )

        if not generated_texts:
            logger.info("No augmentation needed - dataset already balanced.")
            return dataset

        aug_ds = Dataset.from_dict(
            {"text": generated_texts, label_col: generated_labels}
        )
        # Align columns before concatenation.
        base = dataset.select_columns(["text", label_col])
        combined = concatenate_datasets([base, aug_ds]).shuffle(seed=42)

        new_counts = self._class_counts(combined, label_col)
        logger.info(
            "Class counts after augmentation: %s",
            {ID2LABEL.get(k, k): v for k, v in new_counts.items()},
        )
        return combined

    def _generate_samples(self, source_texts: list[str], needed: int) -> list[str]:
        """Generate ``needed`` valid augmented samples from source texts."""
        results: list[str] = []
        idx = 0
        attempts = 0
        max_attempts = needed * 5 + 10

        while len(results) < needed and attempts < max_attempts:
            original = source_texts[idx % len(source_texts)]
            idx += 1
            attempts += 1

            # Alternate strategies to maximize diversity.
            if attempts % 2 == 0:
                candidate = self.synonym_replace(original)
            else:
                candidate = self.back_translate([original])[0]

            if self.verify_augmentation(original, candidate)["is_valid"]:
                results.append(candidate)

        return results

    @staticmethod
    def _class_counts(dataset: Dataset, label_col: str) -> dict[int, int]:
        """Return a ``{label: count}`` mapping for a dataset."""
        counts: dict[int, int] = {}
        for label in dataset[label_col]:
            counts[int(label)] = counts.get(int(label), 0) + 1
        return counts

    def save(self, dataset: Dataset, output_dir: Path) -> None:
        """Persist an augmented dataset to disk in Arrow format."""
        output_dir.mkdir(parents=True, exist_ok=True)
        dataset.save_to_disk(str(output_dir))
        logger.info("Saved augmented dataset to %s", output_dir)


def main() -> None:  # pragma: no cover - integration entry point
    """Augment the processed training split and save it to disk."""
    from datasets import load_from_disk

    settings = get_settings()
    settings.ensure_dirs()

    processed = load_from_disk(str(settings.PROCESSED_DIR))
    train = processed["train"]

    augmenter = SentimentAugmenter(aug_percent=0.15, device="cpu")
    counts = augmenter._class_counts(
        train, "labels" if "labels" in train.column_names else "label"
    )
    target = max(counts.values()) if counts else 0

    balanced = augmenter.augment_minority_classes(train, target_count=target)
    augmenter.save(balanced, settings.AUGMENTED_DIR)


if __name__ == "__main__":  # pragma: no cover
    main()
