"""Bounded same-ledger comparison and isolated checker challenges; no invented human scores."""

import argparse
import json
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from time import perf_counter

from matchlens.api import Question, interpretation_requested, template_question
from matchlens.canonical import candidate_state, run_canonical
from matchlens.claims import build_ledger
from matchlens.evidence_chain import run_evidence_chain, validate_checker
from matchlens.explainer import context_packet
from matchlens.models import Clock
from matchlens.providers import configured_provider
from matchlens.synthetic import generate_match

ROOT = Path(__file__).resolve().parents[1]
POLICIES = ("deterministic", "canonical_single", "evidence_chain")


def file_hash(path):
    return sha256(path.read_text(encoding="utf-8").encode()).hexdigest()


def freeze(path):
    if path.exists():
        raise FileExistsError(path)
    recipe = [
        (5201, "north-6"),
        (5201, "north-8"),
        (5209, "north-6"),
        (5209, "north-8"),
        (5227, "north-7"),
        (5227, "harbor-6"),
    ]
    cases = [
        {
            "id": f"{seed}-{player}",
            "seed": seed,
            "scenario": "shift",
            "request": {
                "period": 2,
                "elapsed_ms": 1500000,
                "anchor_ms": 900000,
                "player_id": player,
                "question": "Why does this passing matter?",
                "language": "en",
                "depth": "casual",
            },
        }
        for seed, player in recipe
    ]
    for name, update in [
        ("causal", {"question": "Did his passing cause the goal?"}),
        ("tracking", {"question": "How fast is he running off-ball?"}),
        ("spanish", {"language": "es", "question": "¿Por qué importan sus pases?"}),
        (
            "zero-window",
            {
                "elapsed_ms": 900000,
                "question": "What changed since the selected moment?",
            },
        ),
    ]:
        cases.append(
            {
                **deepcopy(cases[0]),
                "id": name,
                "request": {**cases[0]["request"], **update},
            }
        )
    paths = list((ROOT / "backend/matchlens").glob("*.py")) + [Path(__file__)]
    manifest = {
        "version": "fair-canonical-v1",
        "scope": "Six fresh eligible passing cases selected for nonempty candidate coverage only; three seeds, three players, two teams. Four deterministic boundaries are reported separately. Not population sampling or independent review.",
        "max_model_calls": 36,
        "policies": POLICIES,
        "ranking": "First eligible candidate in server story ordering; no fitting to human labels.",
        "source_hashes": {p.relative_to(ROOT).as_posix(): file_hash(p) for p in paths},
        "cases": cases,
        "review_status": "Developer-authored checker expectations; human semantic review and viewer usefulness study pending.",
    }
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def load_case(case):
    match = generate_match(case["seed"], case["scenario"])
    request = Question(**case["request"])
    answer = template_question(match.id, request, match)
    context = context_packet(
        match,
        request.player_id,
        Clock(period=request.period, elapsed_ms=request.elapsed_ms),
        request.anchor_ms,
    )
    return request.model_dump(), context, answer


def checker_cases(request, context, trusted):
    ledger = build_ledger(request, context, trusted)
    chosen = ledger["candidates"][0]
    claims = [c for c in ledger["claims"] if c["id"] in chosen["claim_ids"]]
    state = {
        **candidate_state(request, context, ledger),
        "claims": claims,
        "facts": [f for f in ledger["facts"] if f["id"] in chosen["fact_ids"]],
        "counter_evidence": [],
        "publication_rule": "Every claim must be supported, relevant and appropriately limited. A sequence explanation requires an explicit non-causal limitation. Reject missing limitations, wrong scopes or match-wide generalization from one sequence. Do not rewrite.",
    }
    probes = []
    for variant in range(2):
        good = deepcopy(state)
        probes.append(
            {
                "id": f"good-{variant}",
                "kind": "supported_sequence",
                "expected_accept": True,
                "state": good,
            }
        )
        wrong = deepcopy(state)
        wrong["claims"][0]["scope"]["end_ms"] = context["viewer_clock"][
            "elapsed_ms"
        ] + 60000 * (variant + 1)
        probes.append(
            {
                "id": f"scope-{variant}",
                "kind": "wrong_scope",
                "expected_accept": False,
                "state": wrong,
            }
        )
        general = deepcopy(state)
        interpretation = next(
            (c for c in general["claims"] if c["kind"] == "interpretation"),
            general["claims"][0],
        )
        interpretation["text"] = (
            f"{context['player']['name']} was the team's most influential player throughout the match."
            if variant == 0
            else f"This sequence proves {context['player']['name']} consistently controlled the match."
        )
        probes.append(
            {
                "id": f"generalization-{variant}",
                "kind": "overgeneralization",
                "expected_accept": False,
                "state": general,
            }
        )
        missing = deepcopy(state)
        missing["claims"] = [c for c in missing["claims"] if c["kind"] != "limitation"]
        probes.append(
            {
                "id": f"omission-{variant}",
                "kind": "omitted_limitation",
                "expected_accept": False,
                "state": missing,
            }
        )
        # Factually correct player season/roster information is not a passing-sequence explanation.
        irrelevant = deepcopy(state)
        irrelevant["claims"][0]["text"] = (
            f"{context['player']['name']} is listed as a {context['player']['position']} in this synthetic squad."
        )
        irrelevant["claims"][0]["fact_ids"] = ["roster-position"]
        irrelevant["facts"] = [
            {
                "id": "roster-position",
                "subject_id": context["player"]["id"],
                "predicate": "listed_position",
                "value": context["player"]["position"],
                "scope": {"kind": "roster"},
            }
        ]
        probes.append(
            {
                "id": f"irrelevant-{variant}",
                "kind": "irrelevant_but_factual",
                "expected_accept": False,
                "state": irrelevant,
            }
        )
        alternative = deepcopy(state)
        other = next((c for c in ledger["candidates"] if c["id"] != chosen["id"]), None)
        if other:
            alternative["counter_evidence"] = [
                {
                    "candidate": other,
                    "claims": [
                        c for c in ledger["claims"] if c["id"] in other["claim_ids"]
                    ],
                    "facts": [
                        f for f in ledger["facts"] if f["id"] in other["fact_ids"]
                    ],
                    "relationship": "Another sequence; does not refute this specific observed sequence.",
                }
            ]
        probes.append(
            {
                "id": f"non-refutation-{variant}",
                "kind": "supported_with_other_sequence",
                "expected_accept": True,
                "state": alternative,
            }
        )
    return probes


class Recorder:
    def __init__(self, provider, limit):
        self.provider = provider
        self.limit = limit
        self.records = []

    def complete(self, role, state):
        if len(self.records) >= self.limit:
            raise RuntimeError("evaluation_call_limit")
        entry = {
            "role": role,
            "input": deepcopy(state),
            "output": None,
            "error_type": None,
        }
        self.records.append(entry)
        start = perf_counter()
        try:
            entry["output"] = self.provider.complete(role, state)
            return entry["output"]
        except Exception as exc:
            entry["error_type"] = type(exc).__name__
            raise
        finally:
            entry["latency_ms"] = round((perf_counter() - start) * 1000, 2)
            entry["usage"] = getattr(self.provider, "last_usage", None)


def run(manifest_path, output_path, live=False):
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for path, expected in manifest["source_hashes"].items():
        if file_hash(ROOT / path) != expected:
            raise RuntimeError(f"Frozen source changed: {path}")
    if output_path.exists():
        raise FileExistsError(output_path)
    provider = configured_provider() if live else None
    if live and provider is None:
        raise RuntimeError("Authenticated Foundry mode required")
    recorder = Recorder(provider, manifest["max_model_calls"]) if provider else None
    result = {
        "manifest_sha256": file_hash(manifest_path),
        "source_hashes": manifest["source_hashes"],
        "cases": {},
        "rows": [],
        "checker_challenges": [],
        "independent_human_review": None,
        "viewer_study": None,
    }

    def save():
        result["model_calls"] = len(recorder.records) if recorder else 0
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    try:
        for case in manifest["cases"]:
            req, ctx, trusted = load_case(case)
            ledger = build_ledger(req, ctx, trusted)
            result["cases"][case["id"]] = {
                "request": req,
                "context": ctx,
                "ledger": ledger,
            }
            eligible = (
                trusted["intent"] != "unsupported"
                and interpretation_requested(Question(**req), trusted)
                and trusted["intent"] != "change"
                and bool(ledger["candidates"])
                and ledger["coverage"] == "complete"
            )
            for policy in manifest["policies"]:
                first = len(recorder.records) if recorder else 0
                start = perf_counter()
                if eligible and policy != "deterministic" and not live:
                    answer = None
                    status = "skipped_no_live_provider"
                else:
                    selected_provider = (
                        recorder if eligible and policy != "deterministic" else None
                    )
                    answer = (
                        run_evidence_chain
                        if policy == "evidence_chain"
                        else run_canonical
                    )(req, ctx, trusted, selected_provider)
                    status = "completed"
                result["rows"].append(
                    {
                        "case_id": case["id"],
                        "policy": policy,
                        "eligible": eligible,
                        "status": status,
                        "answer": answer,
                        "calls": recorder.records[first:] if recorder else [],
                        "latency_ms": round((perf_counter() - start) * 1000, 2),
                        "human_review": None,
                    }
                )
                save()
                print(case["id"], policy, status, flush=True)
        req, ctx, trusted = load_case(manifest["cases"][0])
        for probe in checker_cases(req, ctx, trusted):
            start = perf_counter()
            first = len(recorder.records) if recorder else 0
            accepted = None
            contract_error = None
            output = None
            if recorder:
                try:
                    output = recorder.complete("checker", probe["state"])
                    validate_checker(
                        output, probe["state"]["claims"], probe["state"]["snapshot_id"]
                    )
                    accepted = True
                except (
                    RuntimeError,
                    ValueError,
                    TimeoutError,
                    KeyError,
                    TypeError,
                ) as exc:
                    contract_error = (
                        str(exc) if isinstance(exc, ValueError) else "provider_failure"
                    )
                    accepted = False if contract_error == "checker_veto" else None
            result["checker_challenges"].append(
                {
                    **probe,
                    "output": output,
                    "accepted": accepted,
                    "contract_error": contract_error,
                    "latency_ms": round((perf_counter() - start) * 1000, 2),
                    "calls": recorder.records[first:] if recorder else [],
                    "human_review": None,
                }
            )
            save()
            print("checker", probe["id"], accepted, contract_error, flush=True)
    finally:
        if hasattr(provider, "close"):
            provider.close()
    print(f"Saved {output_path}; human review remains pending.", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--freeze", type=Path)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()
    if args.freeze:
        freeze(args.freeze)
    else:
        run(args.manifest, args.output, args.live)
