from matchlens.api import Question, template_question
from matchlens.canonical import run_canonical
from matchlens.claims import build_ledger
from matchlens.evidence_chain import validate_checker
from matchlens.explainer import context_packet
from matchlens.models import Clock
from matchlens.synthetic import generate_match


def case():
    match = generate_match(5201, "shift")
    request = Question(
        period=2,
        elapsed_ms=1500000,
        player_id="north-6",
        question="Why does this passing matter?",
    )
    answer = template_question(match.id, request, match)
    context = context_packet(
        match,
        request.player_id,
        Clock(period=2, elapsed_ms=request.elapsed_ms),
        request.anchor_ms,
    )
    return request.model_dump(), context, answer


class Selector:
    def __init__(self, invalid=False):
        self.states = []
        self.invalid = invalid

    def complete(self, role, state):
        assert role == "canonical_selector"
        self.states.append(state)
        return {
            "snapshot_id": state["snapshot_id"],
            "conclusion_id": "invented"
            if self.invalid
            else state["candidates"][-1]["id"],
            "alternative_ids": [],
        }


def test_same_canonical_candidates_one_call_without_extra_output_freedom():
    req, ctx, answer = case()
    provider = Selector()
    result = run_canonical(req, ctx, answer, provider)
    assert len(provider.states) == 1
    ledger = build_ledger(req, ctx, answer)
    assert provider.states[0]["candidates"] == ledger["candidates"]
    chosen = ledger["candidates"][-1]
    assert result["text"] == " ".join(
        c["text"] for c in ledger["claims"] if c["id"] in chosen["claim_ids"]
    )
    assert result["workflow"]["model_calls"] == 1
    assert all(c["checker_verdict"] == "not_run" for c in result["claims"])


def test_deterministic_ranking_and_failure_share_canonical_publication_rules():
    req, ctx, answer = case()
    baseline = run_canonical(req, ctx, answer, None)
    assert baseline["workflow"]["model_calls"] == 0
    bad = run_canonical(req, ctx, answer, Selector(invalid=True))
    assert bad["generation_mode"] == "fallback" and "invented" not in bad["text"]
    blocked = Selector()
    result = run_canonical(req, ctx, answer, blocked, acquire=lambda: False)
    assert not blocked.states and result["generation_mode"] == "fallback"


def test_checker_validation_is_the_same_for_live_checks_and_evaluation():
    import pytest

    proposed = [{"id": "observation"}, {"id": "limit"}]
    accepted = {
        "snapshot_id": "s",
        "verdict": "accept",
        "checks": [
            {
                "claim_id": c["id"],
                "verdict": "supported",
                "reason": "supported_by_facts",
            }
            for c in proposed
        ],
    }
    validate_checker(accepted, proposed, "s")
    with pytest.raises(ValueError):
        validate_checker({**accepted, "snapshot_id": "old"}, proposed, "s")
    with pytest.raises(ValueError):
        validate_checker({**accepted, "checks": accepted["checks"][:-1]}, proposed, "s")


def test_api_can_exercise_one_call_canonical_selection(monkeypatch):
    from fastapi.testclient import TestClient
    from matchlens import api

    monkeypatch.setenv("MATCHLENS_AI_POLICY", "canonical_single")
    provider = Selector()
    monkeypatch.setattr(api, "configured_provider", lambda: provider)
    monkeypatch.setattr(
        api,
        "model_budget",
        lambda: type("Budget", (), {"acquire": lambda self: True})(),
    )
    req, _, _ = case()
    body = (
        TestClient(api.app)
        .post("/api/matches/match-7-shift/questions", json=req)
        .json()
    )
    assert len(provider.states) == 1 and body["workflow"]["kind"] == "canonical_single"
