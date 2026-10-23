"""Fair deterministic/one-call baselines: same ledger and sentence freedoms as the chain."""

from time import perf_counter

from .claims import build_ledger, enrich_answer
from .explainer import interpretation_limit


def candidate_state(request, context, ledger):
    return {
        "snapshot_id": ledger["snapshot_id"],
        "request": request,
        "coverage": ledger["coverage"],
        "source_revision": ledger["source_revision"],
        "viewer_clock": ledger["viewer_clock"],
        "candidates": ledger["candidates"],
        "facts": ledger["facts"],
        "claims": ledger["claims"],
        "aggregate_calculations": ledger["aggregate_calculations"],
        "editorial_context": context["editorial_context"],
    }


def run_canonical(request, context, trusted, provider=None, acquire=None):
    start = perf_counter()
    calls = 0
    selected = None
    reason = None
    alternatives = []
    ledger = build_ledger(request, context, trusted)
    policy = "canonical_single" if provider else "deterministic"
    candidates = {c["id"]: c for c in ledger["candidates"]}
    local_reason = (
        "unsupported_request"
        if trusted.get("intent") == "unsupported"
        else interpretation_limit(request, context) or "comparison_claims_not_enabled"
        if trusted.get("intent") == "change"
        else "no_eligible_evidence"
        if ledger["coverage"] != "complete" or not candidates
        else None
    )
    try:
        if local_reason:
            reason = local_reason
        elif provider:
            if acquire is not None and not acquire():
                raise ValueError("budget_exhausted")
            calls += 1
            output = provider.complete(
                "canonical_selector", candidate_state(request, context, ledger)
            )
            if (
                not isinstance(output, dict)
                or set(output) != {"snapshot_id", "conclusion_id", "alternative_ids"}
                or output["snapshot_id"] != ledger["snapshot_id"]
            ):
                raise ValueError("invalid_selection_contract")
            selected = output["conclusion_id"]
            alternatives = output["alternative_ids"]
            if selected is not None and selected not in candidates:
                raise ValueError("unknown_conclusion")
            if (
                not isinstance(alternatives, list)
                or len(alternatives) > 2
                or len(set(alternatives)) != len(alternatives)
                or any(i not in candidates or i == selected for i in alternatives)
            ):
                raise ValueError("unknown_alternative")
            if selected is None:
                reason = "selector_abstained"
        else:
            # Fixed, declared editorial ranking: server story ordering, no model or tuned labels.
            selected = next(iter(candidates))
    except (RuntimeError, TimeoutError, ValueError, KeyError, TypeError) as exc:
        reason = (
            str(exc) if isinstance(exc, ValueError) else "provider_or_contract_failure"
        )
        selected = None
    if selected:
        chosen = candidates[selected]
        cards = [c for c in ledger["claims"] if c["id"] in chosen["claim_ids"]]
        result = enrich_answer(
            request,
            context,
            {**trusted, "text": " ".join(c["text"] for c in cards)},
            ledger,
            selected,
        )
        result["narrative_evidence"] = [
            s
            for s in context.get("narrative_evidence", [])
            + trusted.get("narrative_evidence", [])
            if s["id"] == chosen["story_id"]
        ][:1]
    else:
        result = enrich_answer(request, context, trusted, ledger)
    return {
        **result,
        "generation_mode": "model"
        if selected and provider
        else "fallback"
        if calls or reason == "budget_exhausted"
        else "template",
        "status": "canonical_selected" if selected else "local_evidence",
        "workflow": {
            "kind": policy,
            "snapshot_id": ledger["snapshot_id"],
            "model_calls": calls,
            "selected_conclusion_id": selected,
            "alternative_ids": alternatives,
            "rejection_reason": reason,
            "stages": [
                {
                    "role": "canonical_selector",
                    "status": "completed"
                    if selected and provider
                    else "not_run"
                    if not calls
                    else "withheld",
                }
            ],
            "latency_ms": round((perf_counter() - start) * 1000, 2),
            "assurance": "Same canonical claim ledger as evidence_chain; no separate model checker.",
        },
    }
