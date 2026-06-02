"""Gradio demo UI for the Sentiment Analysis Engine.

The demo calls the local FastAPI ``/predict`` endpoint and renders the label,
confidence, per-class probabilities, and response time. The API base URL is
configurable via the ``API_URL`` environment variable.
"""

from __future__ import annotations

import os

import gradio as gr
import requests

API_URL = os.environ.get("API_URL", "http://localhost:8000")
_PREDICT_ENDPOINT = f"{API_URL}/predict"

_LABEL_COLORS = {
    "positive": "#16a34a",  # green
    "negative": "#dc2626",  # red
    "neutral": "#6b7280",  # gray
}

_EXAMPLES = [
    ["This is the best purchase I've made all year, absolutely love it!"],
    ["Terrible experience. The product broke after one day and support ignored me."],
    ["The package arrived on Tuesday and contained the items listed on the invoice."],
    ["I'm so happy with the fast shipping and great quality 😍"],
    ["It's okay, nothing special but it does the job."],
]


def _badge_html(label: str, confidence: float) -> str:
    """Render a large colored badge for the predicted label."""
    color = _LABEL_COLORS.get(label, "#374151")
    return (
        f"<div style='display:inline-block;padding:14px 28px;border-radius:12px;"
        f"background:{color};color:white;font-size:28px;font-weight:700;"
        f"text-transform:uppercase;letter-spacing:1px;'>{label}</div>"
        f"<div style='margin-top:10px;font-size:18px;color:#374151;'>"
        f"Confidence: {confidence * 100:.1f}%</div>"
    )


def classify(text: str):
    """Call the FastAPI endpoint and format outputs for the UI.

    Parameters
    ----------
    text:
        User-supplied text.

    Returns
    -------
    tuple
        ``(badge_html, scores_dataframe, response_time_str)``.
    """
    import pandas as pd

    if not text or not text.strip():
        return (
            "<div style='color:#dc2626;'>Please enter some text.</div>",
            pd.DataFrame({"label": [], "probability": []}),
            "",
        )

    try:
        resp = requests.post(_PREDICT_ENDPOINT, json={"text": text}, timeout=30)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as exc:
        return (
            f"<div style='color:#dc2626;'>API error: {exc}</div>",
            pd.DataFrame({"label": [], "probability": []}),
            "",
        )

    badge = _badge_html(data["label"], data["confidence"])
    scores_df = pd.DataFrame(
        {
            "label": list(data["scores"].keys()),
            "probability": [round(v, 4) for v in data["scores"].values()],
        }
    )
    rt = f"{data['processing_time_ms']:.1f} ms"
    return badge, scores_df, rt


def build_demo() -> gr.Blocks:
    """Construct the Gradio Blocks interface."""
    with gr.Blocks(title="Sentiment Analysis Engine") as demo:
        gr.Markdown(
            "# Sentiment Analysis Engine\n"
            "BERT-based 3-class sentiment classification (positive / negative / "
            "neutral) served via FastAPI + ONNX."
        )
        with gr.Row():
            with gr.Column():
                inp = gr.Textbox(
                    label="Text",
                    placeholder="Type a review or tweet ...",
                    lines=4,
                )
                btn = gr.Button("Analyze sentiment", variant="primary")
                gr.Examples(examples=_EXAMPLES, inputs=inp)
            with gr.Column():
                badge = gr.HTML(label="Prediction")
                bar = gr.BarPlot(
                    x="label",
                    y="probability",
                    title="Class probabilities",
                    y_lim=[0, 1],
                )
                rt = gr.Textbox(label="Response time", interactive=False)

        btn.click(fn=classify, inputs=inp, outputs=[badge, bar, rt])
        inp.submit(fn=classify, inputs=inp, outputs=[badge, bar, rt])

    return demo


if __name__ == "__main__":  # pragma: no cover
    build_demo().launch(server_name="0.0.0.0", server_port=7860)
