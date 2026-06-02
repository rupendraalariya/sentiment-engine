"""Model definition for the NLP Sentiment Analysis Engine.

Wraps Hugging Face's :class:`AutoModelForSequenceClassification` with an extra
dropout layer before the classification head and convenience helpers for
probability prediction and joint model/tokenizer persistence.
"""

from __future__ import annotations

from pathlib import Path

import torch
from torch import nn
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    PreTrainedTokenizerBase,
)

from config import ID2LABEL, LABEL2ID, get_settings
from src.logging_utils import get_logger

logger = get_logger(__name__)


class SentimentModel(nn.Module):
    """BERT-based sentiment classifier with an extra dropout layer.

    Parameters
    ----------
    model_name:
        Hugging Face base model identifier.
    num_labels:
        Number of output classes.
    dropout:
        Dropout probability applied before the classifier head.
    pretrained:
        If ``True`` (default) load pretrained weights from the hub. If
        ``False`` build the architecture from config only (random init), which
        avoids downloading large weight files - useful for offline bootstrap.

    Attributes
    ----------
    backbone:
        The underlying ``AutoModelForSequenceClassification``.
    dropout:
        The extra dropout module applied to pooled features.
    tokenizer:
        The associated tokenizer (loaded on construction).
    """

    def __init__(
        self,
        model_name: str = "bert-base-uncased",
        num_labels: int = 3,
        dropout: float = 0.1,
        pretrained: bool = True,
    ) -> None:
        super().__init__()
        self.model_name = model_name
        self.num_labels = num_labels

        if pretrained:
            self.backbone = AutoModelForSequenceClassification.from_pretrained(
                model_name,
                num_labels=num_labels,
                id2label=ID2LABEL,
                label2id=LABEL2ID,
                hidden_dropout_prob=dropout,
            )
        else:
            # Build from config only (random init) - avoids downloading large
            # pretrained weights. Useful for offline bootstrapping/testing.
            from transformers import AutoConfig

            cfg = AutoConfig.from_pretrained(
                model_name,
                num_labels=num_labels,
                id2label=ID2LABEL,
                label2id=LABEL2ID,
                hidden_dropout_prob=dropout,
            )
            self.backbone = AutoModelForSequenceClassification.from_config(cfg)
        # Extra dropout layer in front of the classifier head for regularization.
        self.dropout = nn.Dropout(p=dropout)
        self._inject_dropout()

        self.tokenizer: PreTrainedTokenizerBase = AutoTokenizer.from_pretrained(
            model_name
        )

    def _inject_dropout(self) -> None:
        """Apply the extra dropout immediately before the classifier head.

        Rather than wrapping the classifier in an ``nn.Sequential`` (which would
        rename the classifier's state-dict keys and break ``from_pretrained``
        round-trips), we replace the backbone's existing pre-classifier dropout
        module. This keeps the saved architecture identical to the base model so
        trained classifier weights reload correctly.
        """
        if hasattr(self.backbone, "dropout") and isinstance(
            self.backbone.dropout, nn.Module
        ):
            self.backbone.dropout = self.dropout

    def forward(
        self,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor | None = None,
        token_type_ids: torch.Tensor | None = None,
        labels: torch.Tensor | None = None,
    ):
        """Forward pass delegating to the underlying backbone.

        Returns the standard Hugging Face ``SequenceClassifierOutput`` so the
        model is fully compatible with the :class:`~transformers.Trainer` API.
        """
        return self.backbone(
            input_ids=input_ids,
            attention_mask=attention_mask,
            token_type_ids=token_type_ids,
            labels=labels,
        )

    @torch.no_grad()
    def predict_proba(
        self,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor | None = None,
        token_type_ids: torch.Tensor | None = None,
    ) -> torch.Tensor:
        """Return softmax class probabilities.

        Parameters
        ----------
        input_ids:
            Token id tensor of shape ``(batch, seq_len)``.
        attention_mask:
            Optional attention mask tensor.
        token_type_ids:
            Optional segment id tensor.

        Returns
        -------
        torch.Tensor
            Probability tensor of shape ``(batch, num_labels)``.
        """
        self.eval()
        outputs = self.backbone(
            input_ids=input_ids,
            attention_mask=attention_mask,
            token_type_ids=token_type_ids,
        )
        return torch.softmax(outputs.logits, dim=-1)

    def save(self, path: Path) -> None:
        """Save the backbone weights and tokenizer to ``path``.

        Parameters
        ----------
        path:
            Destination directory. Created if it does not exist.
        """
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        self.backbone.save_pretrained(str(path))
        self.tokenizer.save_pretrained(str(path))
        logger.info("Saved model + tokenizer to %s", path)

    @classmethod
    def load(cls, path: Path) -> "SentimentModel":
        """Load a model + tokenizer previously saved with :meth:`save`.

        Parameters
        ----------
        path:
            Directory containing the saved artifacts.

        Returns
        -------
        SentimentModel
            A reconstructed model instance.
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Model directory not found: {path}")

        settings = get_settings()
        instance = cls.__new__(cls)
        nn.Module.__init__(instance)

        instance.backbone = AutoModelForSequenceClassification.from_pretrained(
            str(path)
        )
        instance.tokenizer = AutoTokenizer.from_pretrained(str(path))
        instance.model_name = getattr(
            instance.backbone.config, "_name_or_path", settings.MODEL_NAME
        )
        instance.num_labels = instance.backbone.config.num_labels
        instance.dropout = nn.Dropout(p=0.1)
        logger.info("Loaded model + tokenizer from %s", path)
        return instance
