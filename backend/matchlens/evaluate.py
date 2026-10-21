"""Paired held-out cases. Human quality ratings stay null until actually reviewed."""

import argparse
import json
from pathlib import Path
from time import perf_counter

from .api import Question, interpretation_requested, template_question
from .explainer import context_packet, explain
from .models import Clock
from .providers import configured_provider
from .synthetic import generate_match
from .workflow import run_workflow

QUESTIONS = [
    ("en", "Why does his passing matter?"),
    ("en", "How many shots has he taken?"),
    ("en", "What changed since the selected moment?"),
    ("en", "Did his passing cause the goal?"),
    ("en", "How fast is he running off-ball?"),
    ("es", "¿Cuántos pases completó?"),
    ("es", "¿Cuántos tiros lleva?"),
    ("es", "¿Qué cambió desde el momento seleccionado?"),
    ("es", "¿Sus pases causaron el gol?"),
    ("es", "¿Cuál es su velocidad?"),
]


def run_evaluation(provider=None, policies=("template", "single", "specialist")):
    rows = []
    for seed, scenario, player, elapsed in [
        (101, "shift", "north-6", 1200000),
        (202, "sparse", "north-12", 1050000),
    ]:
        match = generate_match(seed, scenario)
        for index, (language, question) in enumerate(QUESTIONS):
            request = Question(
                period=2,
                elapsed_ms=elapsed,
                anchor_ms=900000,
                player_id=player,
                question=question,
                language=language,
            )
            trusted = template_question(match.id, request, match)
            packet = context_packet(
                match, player, Clock(period=2, elapsed_ms=elapsed), 900000
            )
            for policy in policies:
                row = {
                    "case_id": f"{seed}-{index}",
                    "seed": seed,
                    "scenario": scenario,
                    "question": question,
                    "language": language,
                    "policy": policy,
                    "factual_support": None,
                    "relevance": None,
                    "appropriate_abstention": None,
                    "cost_usd": None,
                }
                if policy != "template" and provider is None:
                    rows.append(
                        {
                            **row,
                            "status": "skipped_no_live_provider",
                            "latency_ms": None,
                            "usage": None,
                        }
                    )
                    continue
                record_start = len(getattr(provider, "call_records", []))
                diagnostics = []
                start = perf_counter()
                if (
                    policy == "template"
                    or trusted["intent"] == "unsupported"
                    or (
                        policy == "single"
                        and not interpretation_requested(request, trusted)
                    )
                ):
                    answer = {
                        **trusted,
                        "status": "abstain"
                        if trusted["intent"] == "unsupported"
                        else "template",
                    }
                elif policy == "single":
                    answer = explain(
                        request.model_dump(),
                        packet,
                        provider,
                        trusted["text"],
                        diagnostics=diagnostics,
                    )
                else:

                    def fact(answer, name):
                        return [
                            {
                                "id": name,
                                "text": answer["text"],
                                "evidence_ids": answer["evidence_ids"],
                            }
                        ]

                    tools = {
                        "requested_answer": lambda trusted=trusted: fact(
                            trusted, "requested"
                        )
                    }
                    for name, text in {
                        "player_stats": "How involved has he been?",
                        "passing": "How is his passing?",
                        "season_baseline": "Compare his usual season",
                        "change": "What changed since the selected moment?",
                    }.items():
                        tools[name] = (
                            lambda name=name, text=text, match=match, request=request: (
                                fact(
                                    template_question(
                                        match.id,
                                        request.model_copy(update={"question": text}),
                                        match,
                                    ),
                                    name,
                                )
                            )
                        )
                    answer = run_workflow(request.model_dump(), tools, provider)
                rows.append(
                    {
                        **row,
                        "status": "completed",
                        "answer": answer,
                        "latency_ms": round((perf_counter() - start) * 1000, 2),
                        "calls": getattr(provider, "call_records", [])[record_start:],
                        "diagnostics": diagnostics,
                        "usage": [
                            r["usage"]
                            for r in getattr(provider, "call_records", [])[
                                record_start:
                            ]
                            if r["usage"] is not None
                        ],
                    }
                )
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--live",
        action="store_true",
        help="Makes billable requests using configured Foundry credentials",
    )
    parser.add_argument(
        "--output", type=Path, default=Path("artifacts/evaluation.json")
    )
    args = parser.parse_args()
    provider = configured_provider() if args.live else None
    if args.live and provider is None:
        parser.error(
            "Live evaluation requires MATCHLENS_AI_MODE=foundry and project configuration"
        )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    try:
        rows = run_evaluation(provider)
        args.output.write_text(
            json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    finally:
        if hasattr(provider, "close"):
            provider.close()
    print(
        f"Wrote {args.output}; quality ratings and cost require review, not automatic assumptions."
    )


if __name__ == "__main__":
    main()
