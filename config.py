"""Central configuration for the NLP Sentiment Analysis Engine.

All settings are loaded from environment variables (and an optional ``.env``
file) via :class:`Settings`. Paths are resolved relative to the project root so
that nothing is hardcoded to a specific machine.

Usage
-----
>>> from config import get_settings
>>> settings = get_settings()
>>> settings.MODEL_NAME
'bert-base-uncased'
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Project root is the directory that contains this file.
PROJECT_ROOT: Path = Path(__file__).resolve().parent


class Settings(BaseSettings):
    """Application settings, populated from environment / ``.env``.

    Attributes
    ----------
    MODEL_NAME:
        Hugging Face model identifier used for both tokenizer and model.
    NUM_LABELS:
        Number of sentiment classes (negative, neutral, positive).
    MAX_LENGTH:
        Maximum token sequence length used during tokenization.
    BATCH_SIZE:
        Per-device batch size used for training/inference.
    LEARNING_RATE:
        Optimizer learning rate for fine-tuning.
    NUM_EPOCHS:
        Number of training epochs.
    DATA_DIR:
        Root directory for datasets (raw + processed).
    MODEL_DIR:
        Directory where trained model artifacts are written/read.
    """

    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
        # Avoid Pydantic's protected "model_" namespace warnings for MODEL_*.
        protected_namespaces=(),
    )

    # ---- Model / training hyperparameters ----
    MODEL_NAME: str = "bert-base-uncased"
    NUM_LABELS: int = 3
    MAX_LENGTH: int = 128
    BATCH_SIZE: int = 16
    LEARNING_RATE: float = 2e-5
    NUM_EPOCHS: int = 3
    WARMUP_STEPS: int = 500
    WEIGHT_DECAY: float = 0.01

    # ---- Paths ----
    DATA_DIR: Path = Field(default=PROJECT_ROOT / "data")
    MODEL_DIR: Path = Field(default=PROJECT_ROOT / "models")

    # ---- Monitoring / misc ----
    WANDB_PROJECT: str = "sentiment-engine"
    REPORT_TO: str = "none"  # set to "wandb" to enable Weights & Biases
    LOG_LEVEL: str = "INFO"
    TWITTER_CSV: Path = Field(default=PROJECT_ROOT / "data" / "raw" / "twitter.csv")

    # ---- Derived convenience paths ----
    @property
    def RAW_DIR(self) -> Path:
        """Directory holding raw, unprocessed input data."""
        return self.DATA_DIR / "raw"

    @property
    def PROCESSED_DIR(self) -> Path:
        """Directory holding processed Arrow datasets."""
        return self.DATA_DIR / "processed"

    @property
    def AUGMENTED_DIR(self) -> Path:
        """Directory holding the augmented training dataset."""
        return self.PROCESSED_DIR / "train_augmented"

    @property
    def REPORTS_DIR(self) -> Path:
        """Directory for evaluation artifacts (plots, reports)."""
        return PROJECT_ROOT / "reports"

    @field_validator("DATA_DIR", "MODEL_DIR", mode="before")
    @classmethod
    def _resolve_path(cls, value: object) -> Path:
        """Resolve a path-like value to an absolute :class:`Path`.

        Relative paths are interpreted relative to the project root so the
        configuration behaves identically regardless of the current working
        directory.
        """
        if value is None:
            raise ValueError("Path setting cannot be None")
        path = Path(str(value)).expanduser()
        if not path.is_absolute():
            path = PROJECT_ROOT / path
        return path

    def ensure_dirs(self) -> None:
        """Create all directories required by the project if missing."""
        for path in (
            self.DATA_DIR,
            self.RAW_DIR,
            self.PROCESSED_DIR,
            self.MODEL_DIR,
            self.REPORTS_DIR,
        ):
            path.mkdir(parents=True, exist_ok=True)


# Label mapping shared across the whole project.
ID2LABEL: dict[int, str] = {0: "negative", 1: "neutral", 2: "positive"}
LABEL2ID: dict[str, int] = {label: idx for idx, label in ID2LABEL.items()}


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached :class:`Settings` instance.

    Using an LRU cache guarantees a single shared settings object across the
    application without re-reading the environment on every call.
    """
    return Settings()


if __name__ == "__main__":  # pragma: no cover - manual inspection helper
    cfg = get_settings()
    print("Project root:", PROJECT_ROOT)
    for key, value in cfg.model_dump().items():
        print(f"  {key} = {value}")
