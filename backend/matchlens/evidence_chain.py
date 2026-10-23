"""Three bounded role agents over one immutable ledger, with deterministic publication."""

from time import perf_counter

from .claims import build_ledger, enrich_answer
from .explainer import interpretation_limit

ROLES = ("evidence_analysis", "conclusion", "checker")


def run_evidence_chain(request, context, trusted, provider, acquire=None):
    started = perf_counter()
    stages = [{"role": r, "status": "not_run"} for r in ROLES]
    calls = 0
    ledger = None
    reason = None

    def fallback(mode="fallback"):
        answer = (
            enrich_answer(request, context, trusted, ledger=ledger)
            if ledger is not None
            else {
                **trusted,
                "claims": [],
                "primary_evidence_ids": [],
                "aggregate_evidence_ids": trusted.get("evidence_ids", []),
            }
        )
        return {
            **answer,
            "generation_mode": mode,
            "status": "local_evidence" if mode == "template" else "fallback",
            "workflow": {
                "kind": "evidence_chain",
                "snapshot_id": ledger["snapshot_id"] if ledger else None,
                "model_calls": calls,
                "stages": stages,
                "rejection_reason": reason,
                "latency_ms": round((perf_counter() - started) * 1000, 2),
                "assurance": "Canonical facts and editorial rules; model agreement is not independent proof.",
            },
        }

    try:
        ledger = build_ledger(request, context, trusted)
    except (ValueError, KeyError, TypeError):
        reason = "invalid_ledger"
        return fallback()
    if trusted.get("intent") == "unsupported":
        reason = "unsupported_request"
        return fallback("template")
    if trusted.get("intent") == "change" and interpretation_limit(request, context):
        reason = interpretation_limit(request, context)
        return fallback("template")
    if trusted.get("intent") == "change":
        reason = "comparison_claims_not_enabled"
        return fallback("template")
    if provider is None:
        return fallback("template")
    if context["feed_completeness"] != "complete" or not ledger["candidates"]:
        reason = "no_eligible_evidence"
        return fallback("template")
    snapshot = ledger["snapshot_id"]
    candidate_map = {c["id"]: c for c in ledger["candidates"]}
    fact_map = {f["id"]: f for f in ledger["facts"]}
    claim_map = {c["id"]: c for c in ledger["claims"]}

    def call(index, state):
        nonlocal calls, reason
        if acquire is not None and not acquire():
            reason = "budget_exhausted"
            stages[index]["status"] = "budget_blocked"
            raise ValueError(reason)
        calls += 1
        stages[index]["status"] = "running"
        begin = perf_counter()
        try:
            output = provider.complete(ROLES[index], state)
            if not isinstance(output, dict) or output.get("snapshot_id") != snapshot:
                reason = "snapshot_mismatch"
                raise ValueError(reason)
            stages[index]["status"] = "completed"
            return output
        finally:
            stages[index]["latency_ms"] = round((perf_counter() - begin) * 1000, 2)

    try:
        analysis = call(
            0,
            {
                "snapshot_id": snapshot,
                "request": request,
                "aggregate_calculations": ledger["aggregate_calculations"],
                "editorial_context": context["editorial_context"],
                "coverage": ledger["coverage"],
                "source_revision": ledger["source_revision"],
                "viewer_clock": ledger["viewer_clock"],
                "candidates": ledger["candidates"],
                "facts": ledger["facts"],
                "claims": ledger["claims"],
            },
        )
        if set(analysis) != {"snapshot_id", "candidate_ids", "counter_candidate_ids"}:
            raise ValueError("invalid_analysis_contract")
        selected = analysis["candidate_ids"]
        counter = analysis["counter_candidate_ids"]
        if (
            not isinstance(selected, list)
            or not 1 <= len(selected) <= 3
            or len(set(selected)) != len(selected)
            or any(i not in candidate_map for i in selected)
        ):
            raise ValueError("unknown_analysis_candidate")
        if (
            not isinstance(counter, list)
            or len(counter) > 2
            or len(set(counter)) != len(counter)
            or any(i not in candidate_map or i in selected for i in counter)
        ):
            raise ValueError("unknown_counter_evidence")
        stages[0]["candidate_ids"] = selected
        stages[0]["counter_candidate_ids"] = counter
        conclusion = call(
            1,
            {
                "snapshot_id": snapshot,
                "request": request,
                "aggregate_calculations": ledger["aggregate_calculations"],
                "editorial_context": context["editorial_context"],
                "candidates": [candidate_map[i] for i in selected],
                "facts": [
                    fact_map[i]
                    for cid in selected
                    for i in candidate_map[cid]["fact_ids"]
                ],
                "claims": [
                    claim_map[i]
                    for cid in selected
                    for i in candidate_map[cid]["claim_ids"]
                ],
                "counter_evidence": [
                    {
                        "candidate": candidate_map[i],
                        "facts": [fact_map[j] for j in candidate_map[i]["fact_ids"]],
                        "claims": [claim_map[j] for j in candidate_map[i]["claim_ids"]],
                    }
                    for i in counter
                ],
            },
        )
        if (
            set(conclusion) != {"snapshot_id", "conclusion_id"}
            or conclusion["conclusion_id"] not in selected
        ):
            raise ValueError("unapproved_conclusion")
        chosen = candidate_map[conclusion["conclusion_id"]]
        proposed = [claim_map[i] for i in chosen["claim_ids"]]
        stages[1]["conclusion_id"] = chosen["id"]
        stages[1]["claim_ids"] = chosen["claim_ids"]
        checked = call(
            2,
            {
                "snapshot_id": snapshot,
                "request": request,
                "aggregate_calculations": ledger["aggregate_calculations"],
                "editorial_context": context["editorial_context"],
                "source_revision": ledger["source_revision"],
                "viewer_clock": ledger["viewer_clock"],
                "coverage": ledger["coverage"],
                "claims": proposed,
                "facts": [fact_map[i] for i in chosen["fact_ids"]],
                "counter_evidence": [
                    {
                        "candidate": candidate_map[i],
                        "facts": [fact_map[j] for j in candidate_map[i]["fact_ids"]],
                        "claims": [claim_map[j] for j in candidate_map[i]["claim_ids"]],
                    }
                    for i in counter
                ],
                "publication_rule": "Every claim must be supported, relevant and appropriately limited; reject if not. Do not rewrite.",
            },
        )
        checks = validate_checker(checked, proposed, snapshot)
        stages[2]["verdict"] = checked["verdict"]
        stages[2]["checks"] = checks
        # Published sentences are server-authored claim cards; agents cannot replace a number or subject.
        answer = enrich_answer(
            request,
            context,
            {**trusted, "text": " ".join(c["text"] for c in proposed)},
            ledger,
            chosen["id"],
        )
        answer["claims"] = [
            {**c, "checker_verdict": "supported"} for c in answer["claims"]
        ]
        answer["evidence_trail"]["claims"] = answer["claims"]
        story = next(
            s
            for s in context.get("narrative_evidence", [])
            + trusted.get("narrative_evidence", [])
            if s["id"] == chosen["story_id"]
        )
        answer["narrative_evidence"] = [story]
        return {
            **answer,
            "generation_mode": "model",
            "status": "agent_checked_canonical",
            "workflow": {
                "kind": "evidence_chain",
                "snapshot_id": snapshot,
                "model_calls": calls,
                "stages": stages,
                "rejection_reason": None,
                "counter_evidence": [
                    {
                        "candidate": candidate_map[i],
                        "facts": [fact_map[j] for j in candidate_map[i]["fact_ids"]],
                        "claims": [claim_map[j] for j in candidate_map[i]["claim_ids"]],
                    }
                    for i in counter
                ],
                "latency_ms": round((perf_counter() - started) * 1000, 2),
                "assurance": "Three prompts may share one model; not independent verification. Facts are canonically rendered.",
            },
        }
    except (TimeoutError, RuntimeError, ValueError, KeyError, TypeError) as exc:
        if reason is None:
            reason = (
                str(exc)
                if isinstance(exc, ValueError)
                else "provider_or_contract_failure"
            )
        for stage in stages:
            if stage["status"] == "running":
                stage["status"] = "failed"
        return fallback()


def validate_checker(checked, proposed, snapshot):
    if not isinstance(checked, dict) or checked.get("snapshot_id") != snapshot:
        raise ValueError("snapshot_mismatch")
    if set(checked) != {"snapshot_id", "verdict", "checks"} or checked[
        "verdict"
    ] not in {"accept", "reject", "abstain"}:
        raise ValueError("invalid_checker_contract")
    checks = checked["checks"]
    if not isinstance(checks, list) or any(
        not isinstance(c, dict) or set(c) != {"claim_id", "verdict", "reason"}
        for c in checks
    ):
        raise ValueError("invalid_claim_check")
    if len(checks) != len(proposed) or {c["claim_id"] for c in checks} != {
        c["id"] for c in proposed
    }:
        raise ValueError("incomplete_claim_checks")
    if any(
        c["reason"]
        not in {
            "supported_by_facts",
            "irrelevant",
            "wrong_subject",
            "wrong_scope",
            "unsupported_inference",
            "missing_limitation",
        }
        or c["verdict"] not in {"supported", "unsupported", "uncertain"}
        for c in checks
    ):
        raise ValueError("invalid_check_reason")
    if checked["verdict"] != "accept" or any(
        c["verdict"] != "supported" or c["reason"] != "supported_by_facts"
        for c in checks
    ):
        raise ValueError("checker_veto")
    return checks
