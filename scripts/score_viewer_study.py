"""Score voluntary exported viewer answers; QA/developer and incomplete sessions excluded."""

import argparse
import json
from pathlib import Path
from statistics import mean, median


def score(cases, sessions):
    by_id = {c["id"]: c for c in cases}
    seen = set()
    included = []
    excluded = []
    trials = []
    for session in sessions:
        code = session.get("code")
        if code in seen:
            raise ValueError("duplicate_participant_code")
        seen.add(code)
        if session.get("kind") != "study" or session.get("version") != "pilot-v1":
            raise ValueError("unknown_study_version")
        responses = session.get("responses", [])
        if not session.get("complete") or session.get("involved") != "no":
            excluded.append({"code": code, "reason": "incomplete_or_developer_QA"})
            continue
        if session.get("prior_exposure") != "no":
            excluded.append({"code": code, "reason": "prior_exposure_or_unknown"})
            continue
        if len(responses) != len(cases) or {r["case_id"] for r in responses} != set(
            by_id
        ):
            raise ValueError("missing_or_duplicate_situations")
        if (
            sum(r["condition"] == "stats" for r in responses) != 3
            or sum(r["condition"] == "matchlens" for r in responses) != 3
        ):
            raise ValueError("unbalanced_conditions")
        included.append(
            {
                "code": code,
                "familiarity": session.get("familiarity"),
                "independence": "self_report_only",
            }
        )
        for response in responses:
            answers = response["answers"]
            questions = by_id[response["case_id"]]["questions"]
            correct = 0
            for q in questions:
                value = int(answers[q["id"]])
                if not 0 <= value < len(q["options"]):
                    raise ValueError("invalid_answer")
                correct += value == q["correct"]
            elapsed = response["elapsed_ms"]
            confidence = int(answers["confidence"][0])
            if elapsed < 0 or not 1 <= confidence <= 5:
                raise ValueError("invalid_time_or_confidence")
            trials.append(
                {
                    "code": code,
                    "case_id": response["case_id"],
                    "condition": response["condition"],
                    "correct": correct,
                    "questions": len(questions),
                    "elapsed_ms": elapsed,
                    "confidence": confidence,
                    "interrupted": answers.get("interrupted") == "on",
                }
            )
    conditions = {}
    for condition in ("stats", "matchlens"):
        selected = [r for r in trials if r["condition"] == condition]
        uninterrupted = [r for r in selected if not r["interrupted"]]
        conditions[condition] = {
            "trials": len(selected),
            "questions": sum(r["questions"] for r in selected),
            "correct": sum(r["correct"] for r in selected),
            "accuracy": sum(r["correct"] for r in selected)
            / sum(r["questions"] for r in selected)
            if selected
            else None,
            "median_trial_ms_uninterrupted": median(
                r["elapsed_ms"] for r in uninterrupted
            )
            if uninterrupted
            else None,
            "mean_confidence": mean(r["confidence"] for r in selected)
            if selected
            else None,
        }
    return {
        "participants": len(included),
        "included": included,
        "excluded": excluded,
        "conditions": conditions,
        "trials": trials,
        "status": "awaiting_real_participants"
        if not included
        else "small_descriptive_pilot",
        "limitations": "Voluntary self-reported independence; no market-demand inference, significance claim or broad reliability claim. Six situations include paired synthetic variants; trials are not independent population samples. Time includes reading and answering, with interrupted trials excluded from time summaries.",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--cases", type=Path, default=Path("frontend/public/review/study.json")
    )
    parser.add_argument("--responses", type=Path, nargs="*", default=[])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    result = score(
        json.loads(args.cases.read_text(encoding="utf-8"))["cases"],
        [json.loads(p.read_text(encoding="utf-8")) for p in args.responses],
    )
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
