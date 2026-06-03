"""Gradio demo UI for the Sentiment Analysis Engine.

The demo calls the local FastAPI ``/predict`` endpoint and renders the label,
confidence, Google Cloud NLP score/magnitude, per-sentence breakdown, and
response time. The API base URL is configurable via the ``API_URL``
environment variable.
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


def _badge_html(label: str, confidence: float, gcnl_score=None, gcnl_magnitude=None) -> str:
    """Render a large colored badge for the predicted label with score/magnitude."""
    color = _LABEL_COLORS.get(label, "#374151")
    html = (
        f"<div style='display:inline-block;padding:14px 28px;border-radius:12px;"
        f"background:{color};color:white;font-size:28px;font-weight:700;"
        f"text-transform:uppercase;letter-spacing:1px;'>{label}</div>"
        f"<div style='margin-top:10px;font-size:18px;color:#374151;'>"
        f"Confidence: {confidence * 100:.1f}%</div>"
    )
    # Add Google NLP score and magnitude when available
    if gcnl_score is not None and gcnl_magnitude is not None:
        score_color = "#16a34a" if gcnl_score > 0 else "#dc2626" if gcnl_score < 0 else "#6b7280"
        html += (
            f"<div style='margin-top:12px;padding:10px 16px;border-radius:8px;"
            f"background:#f3f4f6;display:inline-block;'>"
            f"<span style='font-size:14px;color:#6b7280;'>Google NLP Score: </span>"
            f"<span style='font-size:18px;font-weight:600;color:{score_color};'>"
            f"{gcnl_score:+.4f}</span>"
            f"<span style='margin-left:16px;font-size:14px;color:#6b7280;'>Magnitude: </span>"
            f"<span style='font-size:18px;font-weight:600;color:#374151;'>"
            f"{gcnl_magnitude:.4f}</span>"
            f"</div>"
        )
    return html


def classify(text: str):
    """Call the FastAPI endpoint and format outputs for the UI.

    Parameters
    ----------
    text:
        User-supplied text.

    Returns
    -------
    tuple
        ``(badge_html, scores_dataframe, sentences_dataframe, response_time_str)``.
    """
    import pandas as pd

    if not text or not text.strip():
        return (
            "<div style='color:#dc2626;'>Please enter some text.</div>",
            pd.DataFrame({"label": [], "probability": []}),
            pd.DataFrame({"sentence": [], "label": [], "score": [], "magnitude": []}),
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
            pd.DataFrame({"sentence": [], "label": [], "score": [], "magnitude": []}),
            "",
        )

    badge = _badge_html(
        data["label"],
        data["confidence"],
        data.get("gcnl_score"),
        data.get("gcnl_magnitude"),
    )
    scores_df = pd.DataFrame(
        {
            "label": list(data["scores"].keys()),
            "probability": [round(v, 4) for v in data["scores"].values()],
        }
    )

    # Per-sentence breakdown (Google Cloud NLP)
    sentences = data.get("sentences") or []
    if sentences:
        sentences_df = pd.DataFrame(
            {
                "sentence": [s["text"] for s in sentences],
                "label": [s["label"] for s in sentences],
                "score": [s["score"] for s in sentences],
                "magnitude": [s["magnitude"] for s in sentences],
            }
        )
    else:
        sentences_df = pd.DataFrame(
            {"sentence": [], "label": [], "score": [], "magnitude": []}
        )

    rt = f"{data['processing_time_ms']:.1f} ms"
    return badge, scores_df, sentences_df, rt


def build_demo() -> gr.Blocks:
    """Construct the Gradio Blocks interface."""
    with gr.Blocks(title="Sentiment Analysis Engine") as demo:
        gr.Markdown(
            "# Sentiment Analysis Engine\n"
            "Powered by **Google Cloud Natural Language API** — returns "
            "sentiment *score* (direction) and *magnitude* (strength) for "
            "accurate, multi-language analysis."
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

        gr.Markdown("### Per-Sentence Sentiment Breakdown")
        sentences_table = gr.Dataframe(
            headers=["sentence", "label", "score", "magnitude"],
            label="Sentence-level analysis (Google Cloud NLP)",
            interactive=False,
        )

        btn.click(
            fn=classify,
            inputs=inp,
            outputs=[badge, bar, sentences_table, rt],
        )
        inp.submit(
            fn=classify,
            inputs=inp,
            outputs=[badge, bar, sentences_table, rt],
        )

    return demo


if __name__ == "__main__":  # pragma: no cover
    build_demo().launch(server_name="0.0.0.0", server_port=7860)
