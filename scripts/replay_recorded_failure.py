"""Replay an actual old model failure through today's guard, with no model call."""

import hashlib
import json
from pathlib import Path

from matchlens.api import Question, template_question
from matchlens.explainer import explain
from matchlens.synthetic import generate_match

root = Path(__file__).resolve().parents[1]
trace = json.loads(
    (root / "docs/evaluations/frozen-v1.json").read_text(encoding="utf-8")
)
original = next(
    r for r in trace["rows"] if r["case_id"] == "1709-1" and r["policy"] == "single"
)
for name in ("models.py", "synthetic.py", "analytics.py"):
    path = f"backend/matchlens/{name}"
    assert (
        hashlib.sha256((root / path).read_text(encoding="utf-8").encode()).hexdigest()
        == trace["source_hashes"][path]
    )


class RecordedResponse:
    def complete(self, role, state):
        return {
            "abstain": False,
            "text": original["answer"]["text"],
            "evidence_ids": original["answer"]["evidence_ids"],
            "rate_basis": original["context"]["rate_contract"]["basis"],
            "team_entry_rate_change": original["context"]["rate_contract"][
                "team_entry_rate_change"
            ],
        }


match = generate_match(1709, "shift")
trusted = template_question(match.id, Question(**original["request"]), match)
result = explain(
    original["request"], original["context"], RecordedResponse(), trusted["text"]
)
assert (
    result["generation_mode"] == "fallback"
    and result["rejection_reason"] == "unsupported_concept"
)
payload = {
    "description": "Actual earlier model output, replayed offline through the current guard. Not new model generation; not a quality benchmark.",
    "case_id": original["case_id"],
    "live_model_calls_for_replay": 0,
    "original_manifest_sha256": trace["manifest_sha256"],
    "original_calls": original["calls"],
    "original_model_text": original["answer"]["text"],
    "guard_replay_result": result,
}
target = root / "frontend/public/evidence/historical-failure.json"
target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
print(
    f"Verified offline guard replay: {result['rejection_reason']}; zero remote model calls. {target}"
)
