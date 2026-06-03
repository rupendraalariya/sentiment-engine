"""Pydantic request/response schemas for the inference API."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

SentimentLabel = Literal["positive", "negative", "neutral"]


class PredictRequest(BaseModel):
    """Request body for a single prediction."""

    text: str = Field(
        ...,
        min_length=1,
        max_length=512,
        description="Input text to classify.",
        examples=["I absolutely love this product!"],
    )


class BatchPredictRequest(BaseModel):
    """Request body for a batch prediction (max 64 items)."""

    texts: list[str] = Field(
        ...,
        min_length=1,
        max_length=64,
        description="List of input texts to classify (1–64 items).",
    )


class SentimentResult(BaseModel):
    """Prediction result for a single text."""

    label: SentimentLabel = Field(
        ..., description="Predicted sentiment label."
    )
    confidence: float = Field(
        ..., ge=0.0, le=1.0,
        description="Probability of the predicted label (0–1).",
    )
    scores: dict[str, float] = Field(
        ..., description="Probability for every class: negative, neutral, positive.",
    )
    processing_time_ms: float = Field(
        ..., ge=0.0, description="Server-side inference time in milliseconds.",
    )


class BatchPredictResponse(BaseModel):
    """Response body for a batch prediction."""

    results: list[SentimentResult] = Field(..., description="Per-text results.")
    total_time_ms: float = Field(
        ..., ge=0.0, description="Total batch processing time in milliseconds.",
    )


class HealthResponse(BaseModel):
    """Response body for the health-check endpoint."""

    status: str = Field(..., description="'ok' or 'degraded'.")
    model: str = Field(..., description="Active model or engine name.")
    device: str = Field(..., description="Compute device: cpu, cuda, or lexicon.")


class MetricsResponse(BaseModel):
    """Response body for the runtime metrics endpoint."""

    total_predictions: int = Field(..., description="Predictions served since startup.")
    average_latency_ms: float = Field(..., description="Mean inference latency (ms).")
    predictions_per_second: float = Field(..., description="Throughput since startup.")
    uptime_seconds: float = Field(..., description="Server uptime in seconds.")
