"""Async tests for the FastAPI inference API.

A lightweight fake inference engine is injected so the tests run without a
trained model or network access. Validation (422) is handled by Pydantic
before the engine is ever touched.
"""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from api import main as api_main
from api.schemas import SentimentResult


class _FakeEngine:
    """Minimal stand-in for :class:`SentimentInferenceEngine`."""

    model_name = "bert-base-uncased"
    device = "cpu"

    def predict(self, text: str) -> SentimentResult:
        if not text or not text.strip():
            raise ValueError("Input text must not be empty.")
        return SentimentResult(
            label="positive",
            confidence=0.99,
            scores={"negative": 0.005, "neutral": 0.005, "positive": 0.99},
            processing_time_ms=1.23,
        )


@pytest.fixture()
async def client():
    """Provide an AsyncClient bound to the app with a fake engine injected."""
    api_main.state.engine = _FakeEngine()  # type: ignore[assignment]
    api_main.state.total_predictions = 0
    api_main.state.total_latency_ms = 0.0
    transport = ASGITransport(app=api_main.app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    api_main.state.engine = None


class TestPredict:
    """Tests for the single-prediction endpoint."""

    async def test_valid_input(self, client) -> None:
        """A valid text returns a well-formed SentimentResult."""
        resp = await client.post("/predict", json={"text": "I love it!"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["label"] in {"positive", "negative", "neutral"}
        assert 0.0 <= body["confidence"] <= 1.0
        assert set(body["scores"].keys()) == {"negative", "neutral", "positive"}

    async def test_empty_string_returns_422(self, client) -> None:
        """An empty string violates min_length and yields 422."""
        resp = await client.post("/predict", json={"text": ""})
        assert resp.status_code == 422


class TestBatch:
    """Tests for the batch endpoint."""

    async def test_batch_valid(self, client) -> None:
        """A small valid batch returns one result per input."""
        resp = await client.post(
            "/predict/batch", json={"texts": ["good", "bad", "ok"]}
        )
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["results"]) == 3
        assert "total_time_ms" in body

    async def test_batch_too_many_items_returns_422(self, client) -> None:
        """A batch of 65 items exceeds the max of 64 and yields 422."""
        resp = await client.post(
            "/predict/batch", json={"texts": ["x"] * 65}
        )
        assert resp.status_code == 422


class TestHealthAndMetrics:
    """Tests for health and metrics endpoints."""

    async def test_health_schema(self, client) -> None:
        """/health returns status, model and device keys."""
        resp = await client.get("/health")
        assert resp.status_code == 200
        body = resp.json()
        assert set(body.keys()) == {"status", "model", "device"}
        assert body["status"] == "ok"

    async def test_metrics_schema(self, client) -> None:
        """/metrics returns the runtime metrics schema."""
        await client.post("/predict", json={"text": "great"})
        resp = await client.get("/metrics")
        assert resp.status_code == 200
        body = resp.json()
        assert set(body.keys()) == {
            "total_predictions",
            "average_latency_ms",
            "predictions_per_second",
            "uptime_seconds",
        }
        assert body["total_predictions"] >= 1
