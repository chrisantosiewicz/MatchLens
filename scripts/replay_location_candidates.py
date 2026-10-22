"""Replay saved model candidates through current guards; never make cloud calls."""

import hashlib
import json
from pathlib import Path

from matchlens.api import Question, template_question
from matchlens.explainer import context_packet, explain
from matchlens.models import Clock
from matchlens.synthetic import generate_match

root = Path(__file__).resolve().parents[1]
manifest = json.loads(
    (root / "docs/frozen-location-v9.json").read_text(encoding="utf-8")
)
trace = json.loads(
    (root / "docs/evaluations/frozen-location-v9.json").read_text(encoding="utf-8")
)
index_path = root / "frontend/public/evidence/index.json"
index = json.loads(index_path.read_text(encoding="utf-8"))
replays = []
for case in manifest["cases"]:
    row = next(
        r
        for r in trace["rows"]
        if r["case_id"] == case["id"] and r["policy"] == "single"
    )
    if not row["calls"]:
        continue
    candidate = (
        {
            "text": row["answer"]["text"],
            "evidence_ids": row["answer"]["model_cited_event_ids"],
            "story_ids": [s["id"] for s in row["answer"]["narrative_evidence"]],
            "rate_basis": row["context"]["rate_contract"]["basis"],
            "team_entry_rate_change": row["context"]["rate_contract"][
                "team_entry_rate_change"
            ],
        }
        if row["answer"]["generation_mode"] == "model"
        else row["diagnostics"][0]["candidate"]
    )
    if candidate is None:
        continue
    match = generate_match(case["seed"], case["scenario"])
    request = Question(**case["request"])
    packet = context_packet(
        match,
        request.player_id,
        Clock(period=request.period, elapsed_ms=request.elapsed_ms),
        request.anchor_ms,
    )
    assert packet["comparison"] == row["context"]["comparison"]
    trusted = template_question(match.id, request, match)

    class Recorded:
        def complete(self, *args, recorded=candidate):
            return recorded

    answer = explain(
        request.model_dump(),
        packet,
        Recorded(),
        trusted["text"],
        trusted_evidence_ids=trusted["evidence_ids"],
        trusted_narrative=trusted["narrative_evidence"],
    )
    assert answer["generation_mode"] == "fallback"
    replay = {
        "description": "Saved candidate replayed offline through current guards, not new model generation.",
        "remote_calls": 0,
        "answer": answer,
    }
    path = root / "frontend/public/evidence" / f"{case['id']}.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["guard_replay"] = replay
    encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode()
    path.write_bytes(encoded)
    next(c for c in index["cases"] if c["id"] == case["id"])["sha256"] = hashlib.sha256(
        encoded
    ).hexdigest()
    replays.append({"case_id": case["id"], **replay})
index["default_case"] = "location-6407.json"
index["semantic_review"] = "location-review-v9.json"
index["workflow_note"] = (
    "Main result shows the current offline guard replay of saved v9 candidates. Original model text remains inspectable. No new model calls for replay."
)
index_path.write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")
report = {
    "remote_calls": 0,
    "source_hashes": {
        p.relative_to(root).as_posix(): hashlib.sha256(
            p.read_text(encoding="utf-8").encode()
        ).hexdigest()
        for p in (root / "backend/matchlens").glob("*.py")
    },
    "replays": replays,
}
(root / "docs/evaluations/location-guard-replay.json").write_text(
    json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)
print(
    f"Replayed {len(replays)} actual saved candidates; current guards returned fallback;0remote calls."
)
