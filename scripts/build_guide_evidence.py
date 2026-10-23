"""Publish recorded guide trial without credentials or invented quality ratings."""

import json
from pathlib import Path
from statistics import median

ROOT = Path(__file__).resolve().parents[1]


def build():
    source = ROOT / "docs/evaluations/viewing-guide-v1.json"
    data = json.loads(source.read_text(encoding="utf-8"))
    calls = [c for row in data["rows"] for c in row["calls"]]
    guides = [r for r in data["rows"] if r["model"]["model_calls"]]
    summary = {
        "version": data["version"],
        "model_calls": len(calls),
        "guide_requests_exercising_model": len(guides),
        "guide_valid_selections": sum(r["model"]["generation_mode"] == "model" for r in guides),
        "guide_median_latency_ms": median(r["model"]["latency_ms"] for r in guides),
        "input_tokens": sum(c["usage"]["input_tokens"] for c in calls),
        "output_tokens": sum(c["usage"]["output_tokens"] for c in calls),
        "independent_human_review": None,
        "incremental_viewer_benefit": None,
        "qualification": "Operational developer-selected trial, not a quality or reliability rate. Changed ranking is not proof of improved ranking. Public app remains template mode.",
    }
    (ROOT / "docs/evaluations/viewing-guide-summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    dest = ROOT / "frontend/public/evidence"
    (dest / "guide-run.json").write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    build()
