"""Inference engine for the NLP Sentiment Analysis Engine.

:class:`SentimentInferenceEngine` loads a fine-tuned model once and serves
single or batched predictions. If an ONNX export is present at
``model_dir/model.onnx`` it is used via ``onnxruntime`` for low-latency, high
throughput inference; otherwise the engine falls back to PyTorch.
"""

from __future__ import annotations

import time
from pathlib import Path

import numpy as np

from api.schemas import SentimentResult
from config import ID2LABEL, get_settings
from src.logging_utils import get_logger

logger = get_logger(__name__)


def _softmax(logits: np.ndarray) -> np.ndarray:
    """Numerically stable softmax over the last axis."""
    shifted = logits - logits.max(axis=-1, keepdims=True)
    exp = np.exp(shifted)
    return exp / exp.sum(axis=-1, keepdims=True)


class SentimentInferenceEngine:
    """Serve sentiment predictions from a fine-tuned model.

    Parameters
    ----------
    model_dir:
        Directory containing the saved model + tokenizer (and optionally
        ``model.onnx``).
    device:
        ``"auto"`` (default), ``"cpu"`` or ``"cuda"``. ``"auto"`` selects CUDA
        when available.
    max_length:
        Maximum token sequence length.

    Attributes
    ----------
    backend:
        Either ``"onnx"`` or ``"pytorch"`` depending on what was loaded.
    model_name:
        Name of the underlying model (for the health endpoint).
    """

    def __init__(
        self,
        model_dir: Path,
        device: str = "auto",
        max_length: int = 128,
    ) -> None:
        self.model_dir = Path(model_dir)
        self.max_length = max_length
        self.device = self._resolve_device(device)
        self.backend = "pytorch"
        self._model = None
        self._session = None

        from transformers import AutoTokenizer

        if not self.model_dir.exists():
            raise FileNotFoundError(
                f"Model directory not found: {self.model_dir}. Train a model "
                "first or mount the weights volume."
            )

        # If the model was bootstrapped (random weights), raise so the API
        # falls back to the lexicon engine.
        flag = self.model_dir / "lexicon_mode.flag"
        if flag.exists():
            raise RuntimeError(
                "Bootstrap (untrained) model detected. "
                "Run `python -m scripts.download_pretrained` to load a "
                "fine-tuned sentiment model."
            )

        self.tokenizer = AutoTokenizer.from_pretrained(str(self.model_dir))
        # Read model name from saved config.json if present.
        import json as _json
        _cfg_path = self.model_dir / "config.json"
        _cfg_raw = _json.loads(_cfg_path.read_text(encoding="utf-8")) if _cfg_path.exists() else {}
        self.model_name = _cfg_raw.get("_name_or_path", get_settings().MODEL_NAME)

        # Read optional sentiment_meta.json for neutral-threshold logic.
        _meta_path = self.model_dir / "sentiment_meta.json"
        if _meta_path.exists():
            meta = _json.loads(_meta_path.read_text(encoding="utf-8"))
            self._neutral_threshold: float = float(meta.get("neutral_threshold", 1.0))
            self._three_class: bool = bool(meta.get("three_class", False))
            self._label_remap: dict = {
                k.lower(): v.lower() for k, v in meta.get("label_remap", {}).items()
            }
        else:
            self._neutral_threshold = 1.0   # disabled
            self._three_class = False
            self._label_remap = {}

        onnx_path = self.model_dir / "model.onnx"
        if onnx_path.exists():
            self._load_onnx(onnx_path)
        else:
            self._load_pytorch()

        # Build id->label from the loaded model config so this works with any
        # pretrained model, not just the training-time bert-base-uncased.
        self._id2label: dict[int, str] = self._resolve_id2label()

        logger.info(
            "Inference engine ready (backend=%s, device=%s, labels=%s).",
            self.backend,
            self.device,
            self._id2label,
        )

    # ------------------------------------------------------------------ #
    # Backend loading
    # ------------------------------------------------------------------ #
    @staticmethod
    def _resolve_device(device: str) -> str:
        """Resolve ``"auto"`` to an actual device string."""
        if device == "auto":
            try:
                import torch

                return "cuda" if torch.cuda.is_available() else "cpu"
            except Exception:  # noqa: BLE001
                return "cpu"
        return device

    def _load_pytorch(self) -> None:
        """Load the PyTorch model from disk."""
        from src.model import SentimentModel

        logger.info("Loading PyTorch model from %s", self.model_dir)
        self._model = SentimentModel.load(self.model_dir)
        self._model.backbone.to(self.device)
        self._model.backbone.eval()
        self.backend = "pytorch"

    def _resolve_id2label(self) -> dict[int, str]:
        """Read the id->label mapping from the loaded model config.

        Falls back to the global ``ID2LABEL`` from config if the model config
        does not carry a valid mapping.  This makes the engine work with any
        pretrained HF classification model, not just those trained in this
        project.
        """
        cfg = None
        if self._model is not None and hasattr(self._model, "backbone"):
            cfg = self._model.backbone.config
        elif self._session is not None:
            # ONNX session — try reading the saved config.json alongside it.
            import json

            cfg_path = self.model_dir / "config.json"
            if cfg_path.exists():
                raw = json.loads(cfg_path.read_text(encoding="utf-8"))
                id2label_raw = raw.get("id2label", {})
                if id2label_raw:
                    return {int(k): str(v) for k, v in id2label_raw.items()}

        if cfg is not None and hasattr(cfg, "id2label") and cfg.id2label:
            return {int(k): str(v).lower() for k, v in cfg.id2label.items()}

        logger.warning("Could not read id2label from model config; using defaults.")
        return dict(ID2LABEL)

    def _load_onnx(self, onnx_path: Path) -> None:
        """Load the ONNX model into an ``onnxruntime`` session."""
        import onnxruntime as ort

        logger.info("Loading ONNX model from %s", onnx_path)
        providers = (
            ["CUDAExecutionProvider", "CPUExecutionProvider"]
            if self.device == "cuda"
            else ["CPUExecutionProvider"]
        )
        self._session = ort.InferenceSession(str(onnx_path), providers=providers)
        self.backend = "onnx"

    # ------------------------------------------------------------------ #
    # Core scoring
    # ------------------------------------------------------------------ #
    def _score(self, texts: list[str]) -> np.ndarray:
        """Return probability matrix of shape ``(len(texts), num_labels)``."""
        encoded = self.tokenizer(
            texts,
            truncation=True,
            padding=True,
            max_length=self.max_length,
            return_tensors="np" if self.backend == "onnx" else "pt",
        )
        if self.backend == "onnx":
            return self._score_onnx(encoded)
        return self._score_pytorch(encoded)

    def _score_onnx(self, encoded) -> np.ndarray:
        """Run inference through the ONNX session."""
        assert self._session is not None
        input_names = {inp.name for inp in self._session.get_inputs()}
        feed = {
            name: encoded[name].astype(np.int64)
            for name in ("input_ids", "attention_mask", "token_type_ids")
            if name in input_names and name in encoded
        }
        logits = self._session.run(None, feed)[0]
        return _softmax(np.asarray(logits))

    def _score_pytorch(self, encoded) -> np.ndarray:
        """Run inference through the PyTorch model."""
        import torch

        assert self._model is not None
        encoded = {k: v.to(self.device) for k, v in encoded.items()}
        with torch.no_grad():
            probs = self._model.predict_proba(
                input_ids=encoded["input_ids"],
                attention_mask=encoded.get("attention_mask"),
                token_type_ids=encoded.get("token_type_ids"),
            )
        return probs.cpu().numpy()

    def _build_result(self, probs: np.ndarray, elapsed_ms: float) -> SentimentResult:
        """Convert a probability vector to a :class:`SentimentResult`.

        When ``sentiment_meta.json`` is present and ``three_class=True``, a
        binary (pos/neg) model is extended to 3-class by treating low-confidence
        predictions as neutral.
        """
        valid = {"positive", "negative", "neutral"}

        if self._three_class and len(probs) == 2:
            # Binary model + neutral-threshold extension.
            best_src_idx = int(np.argmax(probs))
            best_prob = float(probs[best_src_idx])
            src_label = self._id2label.get(best_src_idx, str(best_src_idx)).lower()
            mapped = self._label_remap.get(src_label, src_label)

            if best_prob < self._neutral_threshold:
                label = "neutral"
                # Redistribute: neutral gets the "uncertainty mass".
                neg_p = float(probs[0]) * self._neutral_threshold
                pos_p = float(probs[1]) * self._neutral_threshold
                neu_p = 1.0 - neg_p - pos_p
                scores = {
                    "negative": round(neg_p, 4),
                    "neutral": round(max(neu_p, 0.0), 4),
                    "positive": round(pos_p, 4),
                }
                confidence = scores["neutral"]
            else:
                label = mapped if mapped in valid else "neutral"
                # Scale down the non-neutral classes proportionally.
                neg_p = float(probs[0])
                pos_p = float(probs[1])
                scores = {
                    "negative": round(neg_p, 4),
                    "neutral": round(0.0, 4),
                    "positive": round(pos_p, 4),
                }
                confidence = best_prob
        else:
            # Standard multi-class model.
            best_idx = int(np.argmax(probs))
            num_labels = len(probs)
            scores = {
                self._id2label.get(i, str(i)): float(probs[i])
                for i in range(num_labels)
            }
            label = self._id2label.get(best_idx, str(best_idx))
            if label not in valid:
                label = "neutral"
            confidence = float(probs[best_idx])

        return SentimentResult(
            label=label,  # type: ignore[arg-type]
            confidence=round(confidence, 4),
            scores=scores,
            processing_time_ms=round(elapsed_ms, 3),
        )

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    def predict(self, text: str) -> SentimentResult:
        """Predict the sentiment of a single text.

        Parameters
        ----------
        text:
            Input text.

        Returns
        -------
        SentimentResult
            The prediction with timing information.
        """
        if not text or not text.strip():
            raise ValueError("Input text must not be empty.")
        start = time.perf_counter()
        probs = self._score([text])[0]
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        return self._build_result(probs, elapsed_ms)

    def predict_batch(
        self, texts: list[str], batch_size: int = 32
    ) -> list[SentimentResult]:
        """Predict sentiment for a list of texts using dynamic padding.

        Parameters
        ----------
        texts:
            List of input texts.
        batch_size:
            Number of texts scored per forward pass.

        Returns
        -------
        list[SentimentResult]
            One result per input text, in order.
        """
        if not texts:
            return []

        results: list[SentimentResult] = []
        for start_idx in range(0, len(texts), batch_size):
            chunk = texts[start_idx : start_idx + batch_size]
            start = time.perf_counter()
            probs = self._score(chunk)
            elapsed_ms = (time.perf_counter() - start) * 1000.0
            per_item_ms = elapsed_ms / max(len(chunk), 1)
            for row in probs:
                results.append(self._build_result(row, per_item_ms))
        return results

    def export_to_onnx(self, output_path: Path, opset: int = 14) -> Path:
        """Export the loaded PyTorch model to ONNX.

        Parameters
        ----------
        output_path:
            Destination ``.onnx`` file path.
        opset:
            ONNX opset version (default 14).

        Returns
        -------
        Path
            The path to the written ONNX model.

        Raises
        ------
        RuntimeError
            If the engine is currently backed by ONNX (no PyTorch model loaded).
        """
        import torch

        if self._model is None:
            raise RuntimeError(
                "export_to_onnx requires a PyTorch backend. Re-initialize the "
                "engine without an existing model.onnx file."
            )

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        dummy = self.tokenizer(
            "onnx export dummy input",
            return_tensors="pt",
            padding="max_length",
            truncation=True,
            max_length=self.max_length,
        )
        model = self._model.backbone.to("cpu")
        model.eval()

        dynamic_axes = {
            "input_ids": {0: "batch", 1: "sequence"},
            "attention_mask": {0: "batch", 1: "sequence"},
            "token_type_ids": {0: "batch", 1: "sequence"},
            "logits": {0: "batch"},
        }
        logger.info("Exporting model to ONNX at %s (opset %d)", output_path, opset)
        torch.onnx.export(
            model,
            (
                dummy["input_ids"],
                dummy["attention_mask"],
                dummy["token_type_ids"],
            ),
            str(output_path),
            input_names=["input_ids", "attention_mask", "token_type_ids"],
            output_names=["logits"],
            dynamic_axes=dynamic_axes,
            opset_version=opset,
            do_constant_folding=True,
        )
        logger.info("ONNX export complete.")
        return output_path
