"""FastAPI application exposing the sentiment inference engine.

Endpoints
---------
* ``POST /predict``        - single text prediction.
* ``POST /predict/batch``  - batched prediction (parallelized with asyncio).
* ``GET  /health``         - liveness + model info.
* ``GET  /metrics``        - runtime serving metrics.
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response

from api.schemas import (
    BatchPredictRequest,
    BatchPredictResponse,
    HealthResponse,
    MetricsResponse,
    PredictRequest,
    SentimentResult,
)
from config import get_settings
from src.inference import SentimentInferenceEngine
from src.logging_utils import get_logger

logger = get_logger(__name__)


class _ServingState:
    """Mutable runtime state shared across requests."""

    def __init__(self) -> None:
        self.engine: SentimentInferenceEngine | None = None
        self.start_time: float = time.time()
        self.total_predictions: int = 0
        self.total_latency_ms: float = 0.0

    def record(self, count: int, latency_ms: float) -> None:
        """Record latency for ``count`` predictions."""
        self.total_predictions += count
        self.total_latency_ms += latency_ms


state = _ServingState()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Load the inference engine once at startup and release it on shutdown."""
    settings = get_settings()
    try:
        state.engine = SentimentInferenceEngine(
            model_dir=settings.MODEL_DIR,
            device="auto",
            max_length=settings.MAX_LENGTH,
        )
        logger.info("Inference engine loaded at startup.")
    except Exception as exc:  # noqa: BLE001
        # Keep the app alive so /health can report status; predictions 503.
        logger.error("Failed to load inference engine: %s", exc)
        state.engine = None
    state.start_time = time.time()
    yield
    logger.info("Shutting down; serving stopped.")
    state.engine = None


app = FastAPI(
    title="Sentiment Analysis Engine",
    description="BERT-based 3-class sentiment classification API.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log every request with its method, path, status and duration."""
    start = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = (time.perf_counter() - start) * 1000.0
    logger.info(
        "%s %s -> %d (%.2f ms)",
        request.method,
        request.url.path,
        response.status_code,
        elapsed_ms,
    )
    return response


def _require_engine() -> SentimentInferenceEngine:
    """Return the loaded engine or raise a 503 if unavailable."""
    if state.engine is None:
        raise HTTPException(
            status_code=503,
            detail="Model is not loaded. Train/mount a model and restart.",
        )
    return state.engine


@app.get("/", include_in_schema=False)
async def root() -> JSONResponse:
    """Friendly landing route that lists the available endpoints.

    Visiting the API root in a browser previously returned 404 because only the
    functional endpoints were defined. This route makes the root informative.
    """
    return JSONResponse(
        {
            "service": "Sentiment Analysis Engine",
            "version": app.version,
            "docs": "/docs",
            "endpoints": {
                "POST /predict": "Single text prediction",
                "POST /predict/batch": "Batch prediction (max 64 texts)",
                "GET /health": "Service health and model info",
                "GET /metrics": "Runtime serving metrics",
            },
        }
    )


@app.get("/favicon.ico", include_in_schema=False)
async def favicon() -> Response:
    """Return an empty 204 for favicon requests to avoid noisy 404s."""
    return Response(status_code=204)


@app.post("/predict", response_model=SentimentResult)
async def predict(request: PredictRequest) -> SentimentResult:
    """Predict the sentiment of a single text."""
    engine = _require_engine()
    try:
        result = await asyncio.to_thread(engine.predict, request.text)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        logger.exception("Prediction failed")
        raise HTTPException(status_code=500, detail="Prediction failed.") from exc

    state.record(1, result.processing_time_ms)
    return result


@app.post("/predict/batch", response_model=BatchPredictResponse)
async def predict_batch(request: BatchPredictRequest) -> BatchPredictResponse:
    """Predict sentiment for a batch of texts, processed in parallel."""
    engine = _require_engine()
    start = time.perf_counter()

    async def _one(text: str) -> SentimentResult:
        return await asyncio.to_thread(engine.predict, text)

    try:
        results = await asyncio.gather(*(_one(text) for text in request.texts))
    except Exception as exc:  # noqa: BLE001
        logger.exception("Batch prediction failed")
        raise HTTPException(
            status_code=500, detail="Batch prediction failed."
        ) from exc

    total_ms = (time.perf_counter() - start) * 1000.0
    state.record(len(results), total_ms)
    return BatchPredictResponse(results=list(results), total_time_ms=round(total_ms, 3))


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Return service health and basic model info."""
    engine = state.engine
    return HealthResponse(
        status="ok" if engine is not None else "degraded",
        model=engine.model_name if engine else get_settings().MODEL_NAME,
        device=engine.device if engine else "none",
    )


@app.get("/metrics", response_model=MetricsResponse)
async def metrics() -> MetricsResponse:
    """Return runtime serving metrics since startup."""
    uptime = max(time.time() - state.start_time, 1e-9)
    avg_latency = (
        state.total_latency_ms / state.total_predictions
        if state.total_predictions
        else 0.0
    )
    pps = state.total_predictions / uptime
    return MetricsResponse(
        total_predictions=state.total_predictions,
        average_latency_ms=round(avg_latency, 3),
        predictions_per_second=round(pps, 3),
        uptime_seconds=round(uptime, 3),
    )
