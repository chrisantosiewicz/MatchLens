from copy import deepcopy

from matchlens.api import Question, template_question
from matchlens.claims import build_ledger, enrich_answer
from matchlens.evidence_chain import run_evidence_chain
from matchlens.explainer import context_packet
from matchlens.models import Clock
from matchlens.synthetic import generate_match


def setup():
    match = generate_match(7, "shift")
    request = Question(
        period=2,
        elapsed_ms=1500000,
        player_id="north-6",
        question="Why does his passing matter?",
    )
    answer = template_question(match.id, request, match)
    context = context_packet(
        match,
        request.player_id,
        Clock(period=2, elapsed_ms=request.elapsed_ms),
        request.anchor_ms,
    )
    return request.model_dump(), context, answer


class Scripted:
    def __init__(self, mutate=None):
        self.roles = []
        self.mutate = mutate

    def complete(self, role, state):
        self.roles.append(role)
        if role == "evidence_analysis":
            output = {
                "snapshot_id": state["snapshot_id"],
                "candidate_ids": [state["candidates"][0]["id"]],
                "counter_candidate_ids": [],
            }
        elif role == "conclusion":
            output = {
                "snapshot_id": state["snapshot_id"],
                "conclusion_id": state["candidates"][0]["id"],
            }
        else:
            output = {
                "snapshot_id": state["snapshot_id"],
                "verdict": "accept",
                "checks": [
                    {
                        "claim_id": c["id"],
                        "verdict": "supported",
                        "reason": "supported_by_facts",
                    }
                    for c in state["claims"]
                ],
            }
        return self.mutate(role, state, output) if self.mutate else output


def test_ledger_primary_sources_are_the_sequence_not_all_match_actions():
    req, ctx, answer = setup()
    ledger = build_ledger(req, ctx, answer)
    enriched = enrich_answer(req, ctx, answer)
    assert len(enriched["primary_evidence_ids"]) == 4
    assert set(enriched["primary_evidence_ids"]) < set(answer["evidence_ids"])
    assert len(ledger["snapshot_id"]) == 32
    assert all(e["revision"] == 1 for e in ledger["events"])
    for claim in enriched["claims"]:
        assert claim["fact_ids"] and claim["scope"]
        assert all(id in {f["id"] for f in ledger["facts"]} for id in claim["fact_ids"])


def test_three_roles_have_exact_snapshot_handoffs_and_claim_checks():
    req, ctx, answer = setup()
    provider = Scripted()
    result = run_evidence_chain(req, ctx, answer, provider)
    assert provider.roles == ["evidence_analysis", "conclusion", "checker"]
    assert result["generation_mode"] == "model"
    assert result["status"] == "agent_checked_canonical"
    assert result["claims"] and len(result["primary_evidence_ids"]) == 4
    assert all(c["checker_verdict"] == "supported" for c in result["claims"])
    assert result["evidence_trail"]["snapshot_id"] == result["workflow"]["snapshot_id"]


def test_model_cannot_add_a_different_subject_number_or_unapproved_conclusion():
    req, ctx, answer = setup()
    for change in [
        lambda r, s, o: {**o, "conclusion_id": "invented"} if r == "conclusion" else o,
        lambda r, s, o: (
            {**o, "text": "Mateo completed 999 passes."} if r == "conclusion" else o
        ),
        lambda r, s, o: {**o, "snapshot_id": "stale"} if r == "checker" else o,
    ]:
        result = run_evidence_chain(req, ctx, answer, Scripted(change))
        assert result["generation_mode"] == "fallback"
        assert result["text"] == answer["text"] and "999" not in result["text"]


def test_checker_must_check_every_claim_and_can_veto():
    req, ctx, answer = setup()
    for change in [
        lambda r, s, o: {**o, "checks": o["checks"][:-1]} if r == "checker" else o,
        lambda r, s, o: {**o, "verdict": "reject"} if r == "checker" else o,
    ]:
        result = run_evidence_chain(req, ctx, answer, Scripted(change))
        assert result["generation_mode"] == "fallback"
        assert not any(
            c.get("checker_verdict") == "supported" for c in result["claims"]
        )


def test_future_evidence_is_rejected_before_any_agent_call():
    req, ctx, answer = setup()
    ctx = deepcopy(ctx)
    ctx["narrative_evidence"][0]["sequence"][-1]["elapsed_ms"] = 2700000
    provider = Scripted()
    result = run_evidence_chain(req, ctx, answer, provider)
    assert not provider.roles
    assert result["generation_mode"] == "fallback"
    assert result["workflow"]["rejection_reason"] == "invalid_ledger"


def test_local_mode_has_claim_ledger_without_claiming_agents_ran():
    req, ctx, answer = setup()
    result = run_evidence_chain(req, ctx, answer, None)
    assert result["generation_mode"] == "template"
    assert result["workflow"]["model_calls"] == 0
    assert all(s["status"] == "not_run" for s in result["workflow"]["stages"])
    assert not any(c.get("checker_verdict") == "supported" for c in result["claims"])


def test_each_agent_call_consumes_budget_and_partial_chain_falls_back():
    req, ctx, answer = setup()
    provider = Scripted()
    remaining = [2]

    def acquire():
        remaining[0] -= 1
        return remaining[0] >= 0

    result = run_evidence_chain(req, ctx, answer, provider, acquire=acquire)
    assert provider.roles == ["evidence_analysis", "conclusion"]
    assert result["generation_mode"] == "fallback"
    assert result["workflow"]["rejection_reason"] == "budget_exhausted"


def test_carry_build_up_is_valid_without_a_pass_rank():
    from matchlens.stories import sequence_stories

    req, _ctx, answer = setup()
    match = generate_match(7, "shift")
    story = answer["narrative_evidence"][0]
    first_id = story["evidence_ids"][0]
    changed = [
        e.model_copy(update={"event_type": "carry"}) if e.event_id == first_id else e
        for e in match.events
    ]
    match = match.model_copy(update={"events": changed})
    request = Question(**req)
    result = template_question(match.id, request, match)
    carry = next(
        s
        for s in sequence_stories(
            match, request.player_id, Clock(period=2, elapsed_ms=request.elapsed_ms)
        )
        if s["sequence"][0]["event_type"] == "carry"
    )
    assert carry["pass_rank_before_shot"] is None
    assert result["evidence_trail"]["snapshot_id"]


def test_api_chain_is_opt_in_and_local_mode_records_zero_calls(monkeypatch):
    from fastapi.testclient import TestClient
    from matchlens import api

    monkeypatch.setenv("MATCHLENS_AI_POLICY", "evidence_chain")
    monkeypatch.setenv("MATCHLENS_AI_MODE", "template")
    req, _, _ = setup()
    result = TestClient(api.app).post("/api/matches/match-7-shift/questions", json=req)
    assert result.status_code == 200
    body = result.json()
    assert body["workflow"]["model_calls"] == 0
    assert len(body["primary_evidence_ids"]) == 4
    assert body["generation_mode"] == "template"


def test_api_chain_uses_three_calls_and_counts_do_not_call_models(monkeypatch):
    from fastapi.testclient import TestClient
    from matchlens import api

    monkeypatch.setenv("MATCHLENS_AI_POLICY", "evidence_chain")
    provider = Scripted()
    monkeypatch.setattr(api, "configured_provider", lambda: provider)
    monkeypatch.setattr(
        api,
        "model_budget",
        lambda: type("Budget", (), {"acquire": lambda self: True})(),
    )
    req, _, _ = setup()
    body = (
        TestClient(api.app)
        .post("/api/matches/match-7-shift/questions", json=req)
        .json()
    )
    assert body["generation_mode"] == "model"
    assert len(provider.roles) == 3
    provider.roles.clear()
    req["question"] = "How many passes?"
    body = (
        TestClient(api.app)
        .post("/api/matches/match-7-shift/questions", json=req)
        .json()
    )
    assert not provider.roles and body["generation_mode"] == "template"


def test_legacy_model_output_cannot_inherit_template_claim_badges():
    from matchlens.api import compatible_trace

    _, _, answer = setup()
    assert "claims" in answer
    merged = {
        **compatible_trace(
            answer, {"text": "Another explanation", "generation_mode": "model"}
        ),
        "text": "Another explanation",
    }
    assert "claims" not in merged and "primary_evidence_ids" not in merged


def test_correction_during_checker_withholds_old_agent_conclusion(monkeypatch):
    from fastapi.testclient import TestClient
    from matchlens import api

    monkeypatch.setenv("MATCHLENS_AI_POLICY", "evidence_chain")
    match = generate_match(7, "shift")
    current = [match]
    monkeypatch.setattr(api, "match_or_404", lambda _: current[0])

    def correct(role, state, output):
        if role == "checker":
            events = list(match.events)
            events[0] = events[0].model_copy(
                update={"revision": events[0].revision + 1}
            )
            current[0] = match.model_copy(update={"events": events})
        return output

    monkeypatch.setattr(api, "configured_provider", lambda: Scripted(correct))
    monkeypatch.setattr(
        api,
        "model_budget",
        lambda: type("Budget", (), {"acquire": lambda self: True})(),
    )
    req, _, _ = setup()
    body = (
        TestClient(api.app)
        .post("/api/matches/match-7-shift/questions", json=req)
        .json()
    )
    assert body["status"] == "source_changed" and body["generation_mode"] == "fallback"
    assert all(c["checker_verdict"] == "not_run" for c in body["claims"])


def test_count_answer_does_not_claim_a_different_sequence_was_its_sentence_evidence():
    match = generate_match(7, "shift")
    request = Question(
        period=2, elapsed_ms=1500000, player_id="north-6", question="How many passes?"
    )
    body = template_question(match.id, request, match)
    assert not body["claims"] and not body["primary_evidence_ids"]
    assert body["aggregate_evidence_ids"]


def test_passing_candidates_cannot_be_recovery_stories():
    req, ctx, answer = setup()
    ledger = build_ledger(req, ctx, answer)
    assert ledger["candidates"]
    assert all(c["kind"] != "recovery_followed_by_attack" for c in ledger["candidates"])


def test_change_question_does_not_publish_a_sequence_as_a_comparison():
    match = generate_match(1709, "shift")
    request = Question(
        period=2,
        elapsed_ms=1200000,
        anchor_ms=900000,
        player_id="north-6",
        question="What changed since the selected moment?",
    )
    trusted = template_question(match.id, request, match)
    ctx = context_packet(
        match,
        request.player_id,
        Clock(period=2, elapsed_ms=request.elapsed_ms),
        request.anchor_ms,
    )
    provider = Scripted()
    answer = run_evidence_chain(request.model_dump(), ctx, trusted, provider)
    assert not provider.roles and answer["generation_mode"] == "template"
    assert answer["workflow"]["rejection_reason"] == "comparison_claims_not_enabled"


def test_contradictory_checker_reason_vetoes_supported_verdict():
    req, ctx, answer = setup()

    def contradictory(role, state, output):
        if role == "checker":
            output["checks"] = [{**c, "reason": "irrelevant"} for c in output["checks"]]
        return output

    result = run_evidence_chain(req, ctx, answer, Scripted(contradictory))
    assert result["generation_mode"] == "fallback"
    assert result["workflow"]["rejection_reason"] == "checker_veto"
    assert all(c["checker_verdict"] == "not_run" for c in result["claims"])
