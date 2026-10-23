"""Describe recorded behavior; human semantic quality and usefulness remain unscored."""

import argparse
import json
from pathlib import Path
from statistics import median


def summarize(data):
    policies = {}
    for policy in ("deterministic", "canonical_single", "evidence_chain"):
        rows = [r for r in data["rows"] if r["policy"] == policy]
        exercised = [r for r in rows if r["calls"]]
        calls = [c for r in rows for c in r["calls"]]
        policies[policy] = {
            "eligible_cases": sum(r["eligible"] for r in rows),
            "model_exercised_cases": len(exercised),
            "deterministic_bypasses": sum(not r["eligible"] for r in rows),
            "model_selected_cases": sum(
                (r["answer"] or {}).get("generation_mode") == "model" for r in rows
            ),
            "fallback_cases": sum(
                (r["answer"] or {}).get("generation_mode") == "fallback" for r in rows
            ),
            "calls": len(calls),
            "input_tokens": sum(
                (c.get("usage") or {}).get("input_tokens", 0) for c in calls
            ),
            "output_tokens": sum(
                (c.get("usage") or {}).get("output_tokens", 0) for c in calls
            ),
            "median_exercised_case_ms": round(
                median(r["latency_ms"] for r in exercised), 2
            )
            if exercised
            else None,
        }
    choices = []
    for case_id in data["cases"]:
        rows = [r for r in data["rows"] if r["case_id"] == case_id]
        if not any(r["eligible"] for r in rows):
            continue
        choices.append(
            {
                "case_id": case_id,
                "candidate_count": len(data["cases"][case_id]["ledger"]["candidates"]),
                "selections": {
                    r["policy"]: (r["answer"] or {})
                    .get("evidence_trail", {})
                    .get("selected_conclusion_id")
                    for r in rows
                },
                "texts_identical": len({(r["answer"] or {}).get("text") for r in rows})
                == 1,
                "all_model_policies_completed": all(
                    (r["answer"] or {}).get("generation_mode") == "model"
                    for r in rows
                    if r["policy"] != "deterministic"
                ),
            }
        )
    bad = [p for p in data["checker_challenges"] if not p["expected_accept"]]
    good = [p for p in data["checker_challenges"] if p["expected_accept"]]
    checker = {
        "bad_proposals": len(bad),
        "good_controls": len(good),
        "bad_rejected": sum(p["accepted"] is False for p in bad),
        "bad_accepted": sum(p["accepted"] is True for p in bad),
        "good_accepted": sum(p["accepted"] is True for p in good),
        "good_withheld": sum(p["accepted"] is False for p in good),
        "unresolved_contract_or_provider_errors": sum(
            p["accepted"] is None for p in bad + good
        ),
        "results": [
            {
                "id": p["id"],
                "kind": p["kind"],
                "expected_accept": p["expected_accept"],
                "accepted": p["accepted"],
                "contract_error": p["contract_error"],
            }
            for p in bad + good
        ],
        "interpretation": "Isolated checker probes with developer-authored expectations, including repeated controls. These proposals are not eligible production claims. This does not measure incremental production errors prevented or independent semantic accuracy.",
    }
    return {
        "manifest_sha256": data["manifest_sha256"],
        "policies": policies,
        "choices": choices,
        "checker": checker,
        "independent_human_review": None,
        "viewer_study": None,
        "dollar_cost": None,
        "decision": "No quality winner without independent review. Canonical single is the lower-call alternative; retain local default and do not claim multi-agent superiority.",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    args.output.write_text(
        json.dumps(
            summarize(json.loads(args.input.read_text(encoding="utf-8"))), indent=2
        ),
        encoding="utf-8",
    )
