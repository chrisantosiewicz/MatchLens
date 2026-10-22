"""Run the frozen English capability cases; never invent human review scores."""

import argparse
import hashlib
import json
from pathlib import Path
from time import perf_counter

from matchlens.api import Question, interpretation_requested, template_question
from matchlens.explainer import context_packet, explain
from matchlens.models import Clock
from matchlens.providers import configured_provider
from matchlens.synthetic import generate_match


def digest(path):
    return hashlib.sha256(Path(path).read_text(encoding="utf-8").encode()).hexdigest()


def run(manifest, output, live=False):
    root = Path(__file__).resolve().parents[1]
    specification = json.loads(manifest.read_text(encoding="utf-8"))
    for name, expected in specification["source_hashes"].items():
        if digest(root / name) != expected:
            raise RuntimeError(
                f"Frozen source changed: {name}; preserve old results and create a new candidate"
            )
    if output.exists():
        raise FileExistsError(output)
    provider = configured_provider() if live else None
    if live and provider is None:
        raise RuntimeError("Configure authenticated Foundry mode before --live")
    rows = []
    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        for case in specification["cases"]:
            match = generate_match(case["seed"], case["scenario"])
            request = Question(**case["request"])
            trusted = template_question(match.id, request, match)
            packet = context_packet(
                match,
                request.player_id,
                Clock(period=request.period, elapsed_ms=request.elapsed_ms),
                request.anchor_ms,
            )
            for policy in ("template", "single"):
                start = perf_counter()
                first = len(getattr(provider, "call_records", []))
                diagnostics = []
                needs_model = (
                    policy == "single"
                    and trusted["intent"] != "unsupported"
                    and interpretation_requested(request, trusted)
                )
                if needs_model and provider is None:
                    answer, status = None, "skipped_no_live_provider"
                elif needs_model:
                    answer = explain(
                        request.model_dump(),
                        packet,
                        provider,
                        trusted["text"],
                        diagnostics,
                        trusted_evidence_ids=trusted["evidence_ids"],
                        trusted_narrative=trusted.get("narrative_evidence", []),
                    )
                    status = "completed"
                else:
                    answer, status = trusted, "completed"
                rows.append(
                    {
                        "case_id": case["id"],
                        "request": request.model_dump(),
                        "policy": policy,
                        "status": status,
                        "context": packet,
                        "answer": answer,
                        "calls": getattr(provider, "call_records", [])[first:],
                        "latency_ms": round((perf_counter() - start) * 1000, 2),
                        "diagnostics": diagnostics,
                        "human_review": None,
                    }
                )
                output.write_text(
                    json.dumps(
                        {
                            "manifest_sha256": digest(manifest),
                            "source_hashes": specification["source_hashes"],
                            "rows": rows,
                        },
                        ensure_ascii=False,
                        indent=2,
                    ),
                    encoding="utf-8",
                )
    finally:
        if hasattr(provider, "close"):
            provider.close()
    print(
        f"Saved {len(rows)} rows to {output}; independent human review remains required."
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--manifest", type=Path, default=Path("docs/frozen-english-candidate.json")
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--live", action="store_true", help="Makes bounded billable model requests"
    )
    args = parser.parse_args()
    run(args.manifest, args.output, args.live)
