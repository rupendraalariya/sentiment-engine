"""Data pipeline for the NLP Sentiment Analysis Engine.

This module loads several public sentiment datasets, normalizes them into a
single three-class schema (``0=negative``, ``1=neutral``, ``2=positive``),
cleans the raw text, tokenizes with a BERT tokenizer, computes class weights
for imbalance handling, and finally splits and persists the result to disk in
Arrow format.

Run as a script to execute the full pipeline end-to-end::

    python -m src.data_pipeline
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING

import torch
from datasets import (
    ClassLabel,
    Dataset,
    DatasetDict,
    Value,
    concatenate_datasets,
    load_dataset,
)
from tqdm.auto import tqdm

from config import ID2LABEL, Settings, get_settings
from src.logging_utils import get_logger

if TYPE_CHECKING:  # pragma: no cover - typing only
    from transformers import PreTrainedTokenizerBase

logger = get_logger(__name__)

# ---- Regex patterns (compiled once at import time) ----
_HTML_TAG_RE = re.compile(r"<[^>]+>")
_URL_RE = re.compile(r"(https?://\S+|www\.\S+)")
_WHITESPACE_RE = re.compile(r"\s+")

# Number of neutral samples to synthesize when a source has none.
_DEFAULT_NEUTRAL_SAMPLES = 4000


def clean_text(text: str) -> str:
    """Clean a single raw text string.

    The function removes HTML tags and URLs, normalizes all whitespace to a
    single space, and trims leading/trailing whitespace. Emojis are deliberately
    preserved because they carry sentiment signal.

    Parameters
    ----------
    text:
        Raw input text. Non-string input is coerced to an empty string.

    Returns
    -------
    str
        The cleaned text.

    Examples
    --------
    >>> clean_text("<p>Great product!</p> visit http://x.com")
    'Great product!'
    """
    if not isinstance(text, str):
        return ""
    cleaned = _URL_RE.sub(" ", text)
    cleaned = _HTML_TAG_RE.sub(" ", cleaned)
    cleaned = _WHITESPACE_RE.sub(" ", cleaned)
    return cleaned.strip()


def _to_unified(dataset: Dataset, text_col: str, label_map: dict[int, int]) -> Dataset:
    """Map an arbitrary dataset onto the unified ``[text, label]`` schema.

    Parameters
    ----------
    dataset:
        Source dataset.
    text_col:
        Name of the column containing the text.
    label_map:
        Mapping from the source label id to the unified label id.

    Returns
    -------
    Dataset
        A dataset with exactly two columns: ``text`` (str) and ``label`` (int).
    """

    def _convert(example: dict) -> dict:
        return {
            "text": clean_text(example[text_col]),
            "label": label_map[int(example["label"])],
        }

    remove = [c for c in dataset.column_names if c not in ("text", "label")]
    converted = dataset.map(
        _convert,
        remove_columns=remove,
        desc="unifying schema",
    )
    # Ensure consistent feature types so datasets can be concatenated.
    converted = converted.cast_column("text", Value("string"))
    converted = converted.cast_column("label", Value("int64"))
    return converted


def _load_sst2(max_samples: int = 20000) -> Dataset:
    """Load SST-2 (binary) and map to the unified schema.

    SST-2 labels are ``0=negative``, ``1=positive`` -> mapped to ``0`` and ``2``.
    """
    logger.info("Loading SST-2 from the Hugging Face hub ...")
    ds = load_dataset("glue", "sst2", split="train")
    if max_samples and len(ds) > max_samples:
        ds = ds.shuffle(seed=42).select(range(max_samples))
    return _to_unified(ds, text_col="sentence", label_map={0: 0, 1: 2})


def _load_amazon(max_samples: int = 20000) -> Dataset:
    """Load Amazon Polarity and map to the unified schema.

    Amazon Polarity labels are ``0=negative``, ``1=positive`` -> ``0`` and ``2``.
    """
    logger.info("Loading Amazon Polarity from the Hugging Face hub ...")
    ds = load_dataset("amazon_polarity", split="train")
    if max_samples and len(ds) > max_samples:
        ds = ds.shuffle(seed=42).select(range(max_samples))
    return _to_unified(ds, text_col="content", label_map={0: 0, 1: 2})


def _load_twitter(csv_path: Path, max_samples: int = 20000) -> Dataset | None:
    """Load a Twitter sentiment CSV if present.

    The CSV is expected to contain a text column (one of ``text``/``tweet``/
    ``content``) and a label column (one of ``label``/``sentiment``/``target``).
    Common encodings are normalized to the unified three-class scheme.

    Returns
    -------
    Dataset | None
        ``None`` if the CSV does not exist so the pipeline can continue.
    """
    if not csv_path.exists():
        logger.warning(
            "Twitter CSV not found at %s - skipping this source.", csv_path
        )
        return None

    logger.info("Loading Twitter sentiment CSV from %s ...", csv_path)
    import pandas as pd

    df = pd.read_csv(csv_path, encoding="latin-1")
    df.columns = [c.strip().lower() for c in df.columns]

    text_col = next(
        (c for c in ("text", "tweet", "content", "sentence") if c in df.columns),
        None,
    )
    label_col = next(
        (c for c in ("label", "sentiment", "target", "polarity") if c in df.columns),
        None,
    )
    if text_col is None or label_col is None:
        logger.warning(
            "Twitter CSV missing recognizable text/label columns - skipping."
        )
        return None

    # Normalize a variety of common label encodings to {0,1,2}.
    str_map = {
        "negative": 0,
        "neg": 0,
        "0": 0,
        "neutral": 1,
        "neu": 1,
        "2": 1,
        "positive": 2,
        "pos": 2,
        "4": 2,
        "1": 2,
    }

    def _norm_label(value: object) -> int:
        key = str(value).strip().lower()
        return str_map.get(key, 1)

    df = df[[text_col, label_col]].dropna()
    if max_samples and len(df) > max_samples:
        df = df.sample(n=max_samples, random_state=42)
    df["text"] = df[text_col].astype(str).map(clean_text)
    df["label"] = df[label_col].map(_norm_label).astype("int64")
    df = df[["text", "label"]]

    return Dataset.from_pandas(df, preserve_index=False)


def _synthesize_neutral(n_samples: int = _DEFAULT_NEUTRAL_SAMPLES) -> Dataset:
    """Create simple neutral examples so all three classes are represented.

    Many public sentiment corpora are binary. To guarantee the neutral class
    exists end-to-end, we synthesize factual / neutral statements. These are a
    placeholder; in production replace with a curated neutral corpus.
    """
    templates = [
        "The package arrived on the scheduled delivery date.",
        "The item is gray and made of plastic.",
        "It works as described in the manual.",
        "The meeting is scheduled for three o'clock.",
        "The product measures ten by five centimeters.",
        "I received the order yesterday afternoon.",
        "The device requires two AA batteries.",
        "The store opens at nine in the morning.",
        "The report contains four sections and an appendix.",
        "The software update was installed automatically.",
    ]
    texts = [templates[i % len(templates)] for i in range(n_samples)]
    return Dataset.from_dict({"text": texts, "label": [1] * n_samples})


def load_datasets(settings: Settings | None = None) -> DatasetDict:
    """Load and merge all source datasets into a unified ``DatasetDict``.

    Combines SST-2, Amazon Polarity, an optional Twitter CSV, and synthesized
    neutral samples into a single ``train`` split with columns ``[text, label]``.

    Parameters
    ----------
    settings:
        Optional settings object. Defaults to :func:`config.get_settings`.

    Returns
    -------
    DatasetDict
        A dict with a single ``"train"`` key holding the merged dataset.
    """
    settings = settings or get_settings()
    parts: list[Dataset] = []

    for loader in (_load_sst2, _load_amazon):
        try:
            parts.append(loader())
        except Exception as exc:  # noqa: BLE001 - keep pipeline resilient
            logger.error("Failed to load a source dataset: %s", exc)

    twitter = _load_twitter(settings.TWITTER_CSV)
    if twitter is not None:
        parts.append(twitter)

    # Guarantee the neutral class is present.
    has_neutral = any(1 in set(p.unique("label")) for p in parts)
    if not has_neutral:
        logger.info("No neutral samples found; synthesizing neutral examples.")
        parts.append(_synthesize_neutral())

    if not parts:
        raise RuntimeError(
            "No datasets could be loaded. Check network access and the "
            "Twitter CSV path."
        )

    merged = concatenate_datasets(parts).shuffle(seed=42)
    logger.info("Merged dataset size: %d rows across %d sources.", len(merged), len(parts))
    _log_label_distribution(merged)
    return DatasetDict({"train": merged})


def _log_label_distribution(dataset: Dataset) -> dict[int, int]:
    """Log and return the label distribution of a dataset."""
    labels = dataset["label"]
    counts = {label_id: 0 for label_id in ID2LABEL}
    for label in labels:
        counts[int(label)] = counts.get(int(label), 0) + 1
    pretty = {ID2LABEL[k]: v for k, v in counts.items()}
    logger.info("Label distribution: %s", pretty)
    return counts


def tokenize_dataset(
    dataset: Dataset,
    tokenizer: "PreTrainedTokenizerBase",
    max_length: int = 128,
) -> Dataset:
    """Tokenize a dataset for BERT sequence classification.

    Applies the tokenizer with truncation and ``max_length`` padding, producing
    ``input_ids``, ``attention_mask``, and ``token_type_ids``. The original
    ``label`` column is renamed to ``labels`` to match the Trainer API.

    Parameters
    ----------
    dataset:
        Dataset with a ``text`` and ``label`` column.
    tokenizer:
        A fast BERT tokenizer (``BertTokenizerFast``).
    max_length:
        Maximum sequence length.

    Returns
    -------
    Dataset
        Dataset with columns ``[input_ids, attention_mask, token_type_ids, labels]``.
    """

    def _tokenize(batch: dict) -> dict:
        return tokenizer(
            batch["text"],
            truncation=True,
            padding="max_length",
            max_length=max_length,
        )

    tokenized = dataset.map(
        _tokenize,
        batched=True,
        desc="tokenizing",
        remove_columns=["text"],
    )
    if "label" in tokenized.column_names:
        tokenized = tokenized.rename_column("label", "labels")

    keep = ["input_ids", "attention_mask", "token_type_ids", "labels"]
    keep = [c for c in keep if c in tokenized.column_names]
    tokenized.set_format(type="torch", columns=keep)
    return tokenized


def get_class_weights(dataset: Dataset, num_labels: int = 3) -> torch.Tensor:
    """Compute inverse-frequency class weights for imbalanced data.

    The weight for class ``c`` is ``total / (num_labels * count_c)`` which
    upweights rare classes. Classes with zero samples receive a weight of 0.

    Parameters
    ----------
    dataset:
        Dataset with a label column named ``label`` or ``labels``.
    num_labels:
        Total number of classes.

    Returns
    -------
    torch.Tensor
        A float tensor of shape ``(num_labels,)`` suitable for ``CrossEntropyLoss``.
    """
    label_col = "labels" if "labels" in dataset.column_names else "label"
    labels = dataset[label_col]
    if isinstance(labels, torch.Tensor):
        labels = labels.tolist()

    counts = [0] * num_labels
    for label in labels:
        counts[int(label)] += 1

    total = sum(counts)
    weights = [
        (total / (num_labels * count)) if count > 0 else 0.0 for count in counts
    ]
    tensor = torch.tensor(weights, dtype=torch.float)
    logger.info("Computed class weights: %s", tensor.tolist())
    return tensor


def split_and_save(dataset: Dataset, output_dir: Path) -> DatasetDict:
    """Split a dataset 80/10/10 and persist it to disk as Arrow.

    Parameters
    ----------
    dataset:
        The dataset to split.
    output_dir:
        Directory under which ``train``/``validation``/``test`` are written via
        :meth:`datasets.DatasetDict.save_to_disk`.

    Returns
    -------
    DatasetDict
        The split datasets with keys ``train``, ``validation`` and ``test``.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # 80% train, 20% temp -> split temp into 50/50 (10% val, 10% test).
    first = dataset.train_test_split(test_size=0.2, seed=42)
    second = first["test"].train_test_split(test_size=0.5, seed=42)

    splits = DatasetDict(
        {
            "train": first["train"],
            "validation": second["train"],
            "test": second["test"],
        }
    )
    logger.info(
        "Split sizes -> train=%d, validation=%d, test=%d",
        len(splits["train"]),
        len(splits["validation"]),
        len(splits["test"]),
    )
    splits.save_to_disk(str(output_dir))
    logger.info("Saved processed dataset to %s", output_dir)
    return splits


def main() -> None:
    """Run the full data pipeline end-to-end with progress logging."""
    settings = get_settings()
    settings.ensure_dirs()

    steps = [
        "load datasets",
        "clean + merge",
        "split + save",
    ]
    with tqdm(total=len(steps), desc="data pipeline") as bar:
        bar.set_postfix_str(steps[0])
        dataset_dict = load_datasets(settings)
        bar.update(1)

        bar.set_postfix_str(steps[1])
        merged = dataset_dict["train"]
        # Drop empty texts produced by cleaning.
        merged = merged.filter(lambda ex: bool(ex["text"]), desc="dropping empty")
        bar.update(1)

        bar.set_postfix_str(steps[2])
        split_and_save(merged, settings.PROCESSED_DIR)
        bar.update(1)

    logger.info("Data pipeline complete.")


if __name__ == "__main__":  # pragma: no cover
    main()
