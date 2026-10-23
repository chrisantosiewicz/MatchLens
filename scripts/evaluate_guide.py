"""Bounded operational guide trial; model action selection is not a quality score."""

import argparse
import json
import runpy
from copy import deepcopy
from pathlib import Path

from matchlens.api import Question, template_question
from matchlens.canonical import run_canonical
from matchlens.explainer import context_packet
from matchlens.guide import build_catalog, run_guide
from matchlens.models import Clock
from matchlens.providers import configured_provider
from matchlens.synthetic import generate_match

ROOT = Path(__file__).resolve().parents[1]
helpers = runpy.run_path(str(ROOT / "scripts/evaluate_canonical.py"))
file_hash, Recorder = helpers["file_hash"], helpers["Recorder"]


def freeze(path):
    if path.exists():
        raise FileExistsError(path)
    cases = []
    for name, seed, player, branch, depth, language, scenario in [
        ("attack-fan", 7, "north-6", "attacking", "casual", "en", "shift"),
        ("attack-analyst", 7, "north-6", "attacking", "analyst", "en", "shift"),
        ("defend-fan", 5209, "north-8", "defending", "casual", "en", "shift"),
        ("neutral-analyst", 5227, "harbor-6", "neutral", "analyst", "en", "shift"),
        ("attack-es", 5201, "north-7", "attacking", "casual", "es", "shift"),
        ("defend-es", 5227, "harbor-6", "defending", "casual", "es", "shift"),
        ("sparse", 5209, "north-8", "defending", "casual", "en", "sparse"),
        ("clarify", 7, "north-6", "neutral", "casual", "en", "shift"),
    ]:
        question = (
            "Why do his recorded recoveries matter?"
            if branch == "defending"
            else "How involved has he been?"
            if branch == "neutral"
            else "Why does his passing matter?"
        )
        if language == "es":
            question = (
                "¿Por qué importan sus recuperaciones registradas?"
                if branch == "defending"
                else "¿Por qué importan sus pases?"
            )
        if name == "clarify":
            question = "Is he playing well?"
        cases.append(
            {
                "id": name,
                "seed": seed,
                "scenario": scenario,
                "primary_call": name == "attack-fan",
                "request": {
                    **Question(
                        period=2,
                        elapsed_ms=1500000,
                        anchor_ms=900000,
                        player_id=player,
                        question=question,
                        depth=depth,
                        language=language,
                    ).model_dump(),
                    "branch": branch,
                    "seen_ids": [],
                    "answer_conclusion_id": None,
                },
            }
        )
    paths = list((ROOT / "backend/matchlens").glob("*.py")) + [
        Path(__file__),
        ROOT / "scripts/evaluate_canonical.py",
    ]
    paths += [
        ROOT / "frontend/src" / p
        for p in [
            "App.tsx",
            "contracts.ts",
            "components/ViewingGuide.tsx",
            "components/PlayerPanel.tsx",
        ]
    ]
    path.write_text(
        json.dumps(
            {
                "version": "viewing-guide-v1",
                "max_model_calls": 8,
                "scope": "Developer-selected operational cases, not held-out semantic evaluation. Same eligible catalog for local and model ranking. One analyst-plus-guide pair, three branches, two languages, incomplete coverage and zero-call clarification.",
                "source_hashes": {
                    p.relative_to(ROOT).as_posix(): file_hash(p) for p in paths
                },
                "cases": cases,
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def run(manifest_path, output_path, live=False):
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for path, expected in manifest["source_hashes"].items():
        if file_hash(ROOT / path) != expected:
            raise RuntimeError("Frozen source changed: " + path)
    if output_path.exists():
        raise FileExistsError(output_path)
    provider = configured_provider() if live else None
    if live and provider is None:
        raise RuntimeError("Authenticated Foundry mode required")
    recorder = Recorder(provider, manifest["max_model_calls"]) if provider else None
    result = {
        "version": manifest["version"],
        "manifest_sha256": file_hash(manifest_path),
        "source_hashes": manifest["source_hashes"],
        "rows": [],
        "human_review": None,
        "viewer_benefit": None,
        "scope": manifest["scope"],
    }
    try:
        for case in manifest["cases"]:
            match = generate_match(case["seed"], case["scenario"])
            request = deepcopy(case["request"])
            q = Question(
                **{k: v for k, v in request.items() if k in Question.model_fields}
            )
            context = context_packet(
                match,
                q.player_id,
                Clock(period=q.period, elapsed_ms=q.elapsed_ms),
                q.anchor_ms,
            )
            first = len(recorder.records) if recorder else 0
            primary = None
            if case["primary_call"]:
                primary = run_canonical(
                    q.model_dump(),
                    context,
                    template_question(match.id, q, match),
                    recorder,
                )
                request["answer_conclusion_id"] = primary["workflow"][
                    "selected_conclusion_id"
                ]
            catalog = build_catalog(match, request, context)
            local = run_guide(match, request, context)
            selected = run_guide(match, request, context, recorder) if live else None
            result["rows"].append(
                {
                    "case_id": case["id"],
                    "request": request,
                    "catalog": catalog,
                    "primary_answer": primary,
                    "local": local,
                    "model": selected,
                    "calls": recorder.records[first:] if recorder else [],
                    "human_review": None,
                }
            )
            output_path.parent.mkdir(parents=True, exist_ok=True)
            result["model_calls"] = len(recorder.records) if recorder else 0
            output_path.write_text(
                json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8"
            )
            print(
                case["id"],
                selected["generation_mode"] if selected else "local",
                flush=True,
            )
    finally:
        if provider:
            provider.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["freeze", "run"])
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()
    if args.mode == "freeze":
        freeze(args.manifest)
    else:
        if args.output is None:
            parser.error("--output is required for run")
        run(args.manifest, args.output, args.live)
