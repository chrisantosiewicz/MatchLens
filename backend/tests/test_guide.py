from copy import deepcopy

from matchlens.api import Question, template_question
from matchlens.explainer import context_packet
from matchlens.guide import build_catalog, run_guide
from matchlens.models import Clock
from matchlens.synthetic import generate_match


def setup(branch="attacking", language="en", question="Why does his passing matter?"):
    match = generate_match(7, "shift")
    request = {
        **Question(
            period=2,
            elapsed_ms=1500000,
            player_id="north-6",
            question=question,
            language=language,
        ).model_dump(),
        "branch": branch,
        "seen_ids": [],
        "answer_conclusion_id": None,
    }
    context = context_packet(
        match,
        request["player_id"],
        Clock(period=2, elapsed_ms=request["elapsed_ms"]),
        request["anchor_ms"],
    )
    return match, request, context


class Selector:
    def __init__(self, mutate=None):
        self.calls = []
        self.mutate = mutate

    def complete(self, role, state):
        self.calls.append((role, state))
        output = {
            "snapshot_id": state["snapshot_id"],
            "action_ids": [a["id"] for a in state["actions"][:3]],
        }
        return self.mutate(output) if self.mutate else output


def test_three_knowledge_branches_only_offer_available_evidence_actions():
    for branch in ["attacking", "defending", "neutral"]:
        match, req, ctx = setup(branch)
        catalog = build_catalog(match, req, ctx)
        assert catalog and all(a["branch"] == branch for a in catalog)
        known = {e["event_id"] for e in ctx["audit_events"]}
        assert all(set(a["evidence_ids"]) <= known for a in catalog)
        assert all(
            a["source_version"] == ctx["editorial_context"]["source_revision"]
            for a in catalog
        )


def test_local_clarification_and_spanish_have_no_model_calls():
    match, req, ctx = setup("defending", "es", "¿Está jugando bien?")
    provider = Selector()
    answer = run_guide(match, req, ctx, provider)
    assert not provider.calls and answer["clarification"]
    assert answer["generation_mode"] == "template" and len(answer["cards"]) <= 3
    assert any(
        "recuper" in (a["title"] + a.get("body", "")).lower() for a in answer["cards"]
    )


def test_one_optional_call_can_only_rank_known_actions():
    match, req, ctx = setup()
    provider = Selector()
    result = run_guide(match, req, ctx, provider)
    assert [r for r, _ in provider.calls] == ["viewing_guide"]
    assert result["generation_mode"] == "model" and result["model_calls"] == 1
    assert result["cards"]
    for mutation in [
        lambda o: {**o, "action_ids": ["invented"]},
        lambda o: {**o, "text": "He controlled midfield"},
        lambda o: {**o, "snapshot_id": "old"},
        lambda o: {**o, "action_ids": [o["action_ids"][0]] * 2},
    ]:
        bad = run_guide(match, req, ctx, Selector(mutation))
        assert bad["generation_mode"] == "fallback" and bad["cards"]
        assert "controlled midfield" not in str(bad["cards"])


def test_incomplete_feed_never_offers_sequence_or_comparison_and_budget_is_bounded():
    match, req, ctx = setup()
    match = match.model_copy(update={"feed_completeness": "incomplete"})
    ctx = deepcopy(ctx)
    ctx["feed_completeness"] = "incomplete"
    ctx["editorial_context"]["coverage"] = "incomplete"
    cards = build_catalog(match, req, ctx)
    assert not any(c["kind"] in {"sequence", "comparison"} for c in cards)
    provider = Selector()
    result = run_guide(match, req, ctx, provider, acquire=lambda: False)
    assert not provider.calls and result["generation_mode"] == "fallback"


def test_seen_actions_and_unknown_answer_anchor_do_not_generate_new_claims():
    match, req, ctx = setup()
    catalog = build_catalog(match, req, ctx)
    req["seen_ids"] = [catalog[0]["id"]]
    assert catalog[0]["id"] not in {a["id"] for a in build_catalog(match, req, ctx)}
    req["answer_conclusion_id"] = "invented"
    provider = Selector()
    result = run_guide(match, req, ctx, provider)
    assert not provider.calls and result["rejection_reason"] == "unknown_answer_anchor"


def test_seen_sequences_do_not_hide_different_branch_stories_or_block_more_stories():
    match, req, _ = setup()
    match = generate_match(0, "shift")
    req["elapsed_ms"] = 2700000
    ctx = context_packet(
        match, req["player_id"], Clock(period=2, elapsed_ms=2700000), req["anchor_ms"]
    )
    attacking = [c for c in build_catalog(match, req, ctx) if c["kind"] == "sequence"]
    defending_req = {**req, "branch": "defending"}
    defending = [
        c for c in build_catalog(match, defending_req, ctx) if c["kind"] == "sequence"
    ]
    assert attacking[0]["story_id"] != defending[0]["story_id"]
    defending_req["seen_ids"] = [attacking[0]["id"]]
    assert defending[0]["story_id"] in {
        c.get("story_id") for c in build_catalog(match, defending_req, ctx)
    }
    req["seen_ids"] = [c["id"] for c in attacking]
    further = [c for c in build_catalog(match, req, ctx) if c["kind"] == "sequence"]
    assert further and not {c["story_id"] for c in further} & {
        c["story_id"] for c in attacking
    }


def test_broad_and_defensive_questions_are_relevant_local_answers():
    match, _, _ = setup()
    broad = template_question(
        match.id,
        Question(
            period=2,
            elapsed_ms=1500000,
            player_id="north-6",
            question="Is he playing well?",
        ),
        match,
    )
    assert broad["intent"] == "clarify" and not broad["evidence_ids"]
    defensive = template_question(
        match.id,
        Question(
            period=2,
            elapsed_ms=1500000,
            player_id="north-6",
            question="Show his recorded recoveries and tackles",
        ),
        match,
    )
    assert defensive["intent"] == "defending" and "recover" in defensive["text"].lower()
    assert "shot_build_up" not in str(defensive["claims"])


def test_guidance_api_rejects_stale_source_without_a_model_call(monkeypatch):
    from fastapi.testclient import TestClient
    from matchlens import api

    def forbidden():
        raise AssertionError("No model for stale requests")

    monkeypatch.setattr(api, "configured_provider", forbidden)
    _match, req, _ = setup()
    req["expected_source_version"] = "old"
    response = TestClient(api.app).post("/api/matches/match-7-shift/guidance", json=req)
    assert response.status_code == 409


def test_guidance_api_withholds_correction_during_model_selection(monkeypatch):
    from fastapi.testclient import TestClient
    from matchlens import api

    match, req, _ = setup()
    current = [match]
    monkeypatch.setattr(api, "match_or_404", lambda _: current[0])

    class Correcting(Selector):
        def complete(self, role, state):
            output = super().complete(role, state)
            events = list(match.events)
            events[0] = events[0].model_copy(update={"revision": 2})
            current[0] = match.model_copy(update={"events": events})
            return output

    monkeypatch.setattr(api, "configured_provider", lambda: Correcting())
    monkeypatch.setattr(
        api,
        "model_budget",
        lambda: type("Budget", (), {"acquire": lambda self: True})(),
    )
    response = TestClient(api.app).post("/api/matches/match-7-shift/guidance", json=req)
    assert response.status_code == 409


def test_defensive_canonical_ledger_excludes_attack_only_sequences():
    from matchlens.claims import build_ledger

    match, req, ctx = setup(
        "defending", question="Why do his recorded recoveries matter?"
    )
    answer = template_question(
        match.id,
        Question(**{k: v for k, v in req.items() if k in Question.model_fields}),
        match,
    )
    ledger = build_ledger(req, ctx, answer)
    assert all(
        c["kind"] in {"recovery_followed_by_attack", "turnover_then_opposition_shot"}
        for c in ledger["candidates"]
    )
