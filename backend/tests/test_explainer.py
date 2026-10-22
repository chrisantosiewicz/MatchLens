from matchlens.analytics import compare_windows, player_stats
from matchlens.explainer import context_packet, explain
from matchlens.models import Clock
from matchlens.synthetic import generate_match


def packet():
    match = generate_match(101, "shift")
    return context_packet(match, "north-6", Clock(period=2, elapsed_ms=1200000), 900000)


def test_packet_is_clock_limited_and_contains_calculated_windows():
    p = packet()
    match = generate_match(101, "shift")
    clock = Clock(period=2, elapsed_ms=1200000)
    assert p["player_stats"] == player_stats(match.events, "north-6", clock)
    assert p["comparison"] == compare_windows(
        match.events, Clock(period=2, elapsed_ms=900000), clock, "north"
    )
    assert p["comparison"]["after"]["duration_ms"] == 300000
    assert "not causation" in p["limits"]
    assert all((e["period"], e["elapsed_ms"]) <= (2, 1200000) for e in p["events"])


def test_single_model_can_interpret_context_but_unknown_sources_fall_back():
    class Model:
        def complete(self, role, state):
            assert role == "explainer"
            return {
                "rate_basis": state["context"]["rate_contract"]["basis"],
                "team_entry_rate_change": state["context"]["rate_contract"][
                    "team_entry_rate_change"
                ],
                "text": "A useful progression contribution, with a limited observation window.",
                "evidence_ids": [state["context"]["metric_sources"][0]],
            }

    p = packet()
    answer = explain(
        {"question": "Why does his passing matter?"}, p, Model(), "Trusted answer."
    )
    assert answer["generation_mode"] == "model"
    assert "limited observation" in answer["text"]
    before = next(
        c
        for c in answer["fact_support"]
        if c["metric"] == "team_box_entries" and c["window"] == "before"
    )
    after = next(
        c
        for c in answer["fact_support"]
        if c["metric"] == "team_box_entries" and c["window"] == "after"
    )
    assert (before["count"], before["minutes"], before["rate"]) == (2, 10, 0.2)
    assert (after["count"], after["minutes"], after["rate"]) == (3, 5, 0.6)
    assert len(before["source_ids"]) == 2 and len(after["source_ids"]) == 3
    assert set(before["source_ids"] + after["source_ids"]) <= set(
        answer["evidence_ids"]
    )
    assert len(answer["model_cited_event_ids"]) == 1
    assert "closer to goal" in answer["metric_definition"]

    class Invented:
        def complete(self, role, state):
            return {"text": "Completed 999 passes.", "evidence_ids": ["invented"]}

    answer = explain({}, p, Invented(), "Trusted answer.")
    assert answer["generation_mode"] == "fallback"
    assert answer["text"] == "Trusted answer."


def test_timeout_and_explicit_abstention_are_distinct():
    class Timeout:
        def complete(self, role, state):
            raise TimeoutError()

    class Abstain:
        def complete(self, role, state):
            return {"abstain": True}

    assert explain({}, packet(), Timeout(), "Trusted.")["generation_mode"] == "fallback"
    assert explain({}, packet(), Abstain(), "Trusted.")["status"] == "abstain"


def test_numeric_equivalence_is_allowed_but_rounding_and_id_digits_are_not():
    p = packet()
    p["contributions_after"]["pass_completion"] = 100.0
    p["player_stats"]["pass_completion"] = 89.2
    p["events"][0]["event_id"] = "event-999"

    class Model:
        def __init__(self, text):
            self.text = text

        def complete(self, role, state):
            return {
                "text": self.text,
                "evidence_ids": ["event-999"],
                "rate_basis": state["context"]["rate_contract"]["basis"],
                "team_entry_rate_change": state["context"]["rate_contract"][
                    "team_entry_rate_change"
                ],
            }

    assert (
        explain({}, p, Model("100% completion in the after window."), "Trusted.")[
            "generation_mode"
        ]
        == "model"
    )
    assert (
        explain({}, p, Model("50-60 minutes before; 60–65 minutes after."), "Trusted.")[
            "generation_mode"
        ]
        == "model"
    )
    for text in [
        "89% completion.",
        "999 completed passes.",
        "-100% completion.",
        "−100% completion.",
    ]:
        answer = explain({}, p, Model(text), "Trusted.")
        assert answer["generation_mode"] == "fallback"
        assert answer["rejection_reason"] == "unknown_number"


def test_diagnostics_preserve_rejected_output_without_changing_fallback():
    class Model:
        def complete(self, role, state):
            return {"text": "Unsupported claim.", "evidence_ids": ["unknown"]}

    diagnostics = []
    answer = explain({}, packet(), Model(), "Trusted.", diagnostics=diagnostics)
    assert answer["text"] == "Trusted."
    assert answer["rejection_reason"] == "unknown_evidence"
    assert diagnostics[0]["candidate"]["text"] == "Unsupported claim."
    assert "candidate" not in answer


def test_model_must_use_calculated_rate_direction_for_unequal_windows():
    p = packet()
    p["rate_contract"] = {
        "basis": "per_minute",
        "team_entry_rate_change": "unchanged",
        "before": 0.4,
        "after": 0.4,
    }

    class Misleading:
        def complete(self, role, state):
            return {
                "text": "The team entry rate decreased.",
                "evidence_ids": [p["events"][0]["event_id"]],
                "rate_basis": "raw_counts",
                "team_entry_rate_change": "decreased",
            }

    answer = explain({}, p, Misleading(), "Trusted.")
    assert answer["generation_mode"] == "fallback"
    assert answer["rejection_reason"] == "invalid_rate_comparison"


def test_substitute_rates_use_active_minutes_and_zero_window_is_unrated():
    match = generate_match(202, "sparse")
    p = context_packet(match, "north-12", Clock(period=2, elapsed_ms=1200000), 900000)
    assert p["feed_completeness"] == "incomplete"
    assert p["player_window_minutes"] == {"before": 0, "after": 5}
    assert p["player_rates"]["before"]["actions_per_minute"] is None
    p = context_packet(match, "north-12", Clock(period=2, elapsed_ms=900000), 900000)
    assert p["player_rates"]["after"]["actions_per_minute"] is None


def test_interpretation_does_not_call_model_for_incomplete_or_zero_windows():
    class Forbidden:
        def complete(self, *args):
            raise AssertionError("Insufficient context should stay deterministic")

    sparse = generate_match(1741, "sparse")
    contexts = [
        context_packet(sparse, "north-12", Clock(period=2, elapsed_ms=1050000), 900000),
        context_packet(
            generate_match(1709, "shift"),
            "north-6",
            Clock(period=2, elapsed_ms=900000),
            900000,
        ),
        context_packet(
            generate_match(1753, "shift"),
            "north-12",
            Clock(period=2, elapsed_ms=1200000),
            900000,
        ),
    ]
    for context in contexts:
        answer = explain(
            {"question": "What changed since the selected moment?"},
            context,
            Forbidden(),
            "Trusted observed facts.",
        )
        assert answer["generation_mode"] == "template"
        assert answer["status"] == "limited_input"


def test_rate_facts_cannot_authorize_speed_or_off_ball_interpretations():
    class Model:
        def complete(self, role, state):
            context = state["context"]
            return {
                "text": "This indicates increased offensive penetration speed.",
                "evidence_ids": [context["metric_sources"][0]],
                "rate_basis": context["rate_contract"]["basis"],
                "team_entry_rate_change": context["rate_contract"][
                    "team_entry_rate_change"
                ],
            }

    result = explain({}, packet(), Model(), "Trusted observed facts.")
    assert result["generation_mode"] == "fallback"
    assert result["rejection_reason"] == "unsupported_concept"


def test_selected_story_requires_complete_sources_and_exact_visible_clocks():
    p = packet()
    assert p["narrative_evidence"]
    story = p["narrative_evidence"][0]

    class Model:
        def __init__(self, ids, text, story_ids):
            self.ids, self.text, self.story_ids = ids, text, story_ids

        def complete(self, role, state):
            return {
                "text": self.text,
                "evidence_ids": self.ids,
                "story_ids": self.story_ids,
                "rate_basis": p["rate_contract"]["basis"],
                "team_entry_rate_change": p["rate_contract"]["team_entry_rate_change"],
            }

    good = Model(
        story["evidence_ids"],
        f"Recorded build-up at {story['action_clock']}; sequence involvement is not an assist.",
        [story["id"]],
    )
    assert explain({}, p, good, "Trusted.")["narrative_evidence"] == [story]
    partial = Model(story["evidence_ids"][:1], "Recorded involvement.", [story["id"]])
    assert (
        explain({}, p, partial, "Trusted.")["rejection_reason"]
        == "incomplete_story_evidence"
    )
    future = Model(story["evidence_ids"], "Recorded build-up at 89:59.", [story["id"]])
    assert explain({}, p, future, "Trusted.")["rejection_reason"] == "unknown_clock"
    invented = Model(story["evidence_ids"], "Recorded involvement.", ["invented"])
    assert explain({}, p, invented, "Trusted.")["rejection_reason"] == "unknown_story"


def test_model_receives_curated_football_facts_not_coordinates_or_unrelated_action_totals():
    p = packet()

    class Inspect:
        def complete(self, role, state):
            context = state["context"]
            assert "events" not in context and "player_stats" not in context
            assert "contributions_after" not in context
            assert context["player_name"] == p["player"]["name"]
            assert context["narrative_evidence"][0]["evidence_ids"]
            assert "sequence" not in context["narrative_evidence"][0]
            return {"abstain": True}

    assert explain({}, p, Inspect(), "Trusted.")["status"] == "abstain"


def test_connecting_action_word_is_not_confused_with_an_all_action_rate():
    p = packet()

    class Model:
        def __init__(self, text):
            self.text = text

        def complete(self, role, state):
            return {
                "text": self.text,
                "evidence_ids": [p["events"][0]["event_id"]],
                "rate_basis": p["rate_contract"]["basis"],
                "team_entry_rate_change": p["rate_contract"]["team_entry_rate_change"],
            }

    assert (
        explain(
            {},
            p,
            Model("A recorded connecting action in a shot-ending sequence."),
            "Trusted.",
        )["generation_mode"]
        == "model"
    )
    assert (
        explain({}, p, Model("His action rate per minute increased."), "Trusted.")[
            "rejection_reason"
        ]
        == "unsupported_concept"
    )


def test_narrative_stays_inside_comparison_window_even_when_viewer_is_later():
    p = context_packet(
        generate_match(7, "shift"),
        "north-6",
        Clock(period=2, elapsed_ms=2700000),
        900000,
    )
    assert p["narrative_evidence"]
    assert all(
        e["elapsed_ms"] <= 1500000
        for s in p["narrative_evidence"]
        for e in s["sequence"]
    )


def test_fallback_retains_the_teammate_events_behind_its_story():
    p = packet()

    class Timeout:
        def complete(self, *args):
            raise TimeoutError()

    result = explain({}, p, Timeout(), "Trusted sequence explanation.")
    assert set(p["narrative_evidence"][0]["evidence_ids"]) <= set(
        result["evidence_ids"]
    )
    assert result["narrative_evidence"] == p["narrative_evidence"][:1]


def test_recorded_location_trial_subject_and_metric_errors_are_rejected():
    import json
    from pathlib import Path

    rows = json.loads(
        (
            Path(__file__).resolve().parents[2]
            / "docs/evaluations/frozen-location-v8.json"
        ).read_text(encoding="utf-8")
    )["rows"]
    expected = {
        "location-6301": "unsupported_sequence_attribution",
        "location-6303": "unapproved_rate_claim",
        "location-6307": "causal_sequence_wording",
    }
    for row in rows:
        if row["policy"] != "single" or row["case_id"] not in expected:
            continue

        class Recorded:
            def complete(self, *args, recorded_row=row):
                answer = recorded_row["answer"]
                ctx = recorded_row["context"]
                return {
                    "text": answer["text"],
                    "evidence_ids": answer["model_cited_event_ids"],
                    "story_ids": [s["id"] for s in answer["narrative_evidence"]],
                    "rate_basis": ctx["rate_contract"]["basis"],
                    "team_entry_rate_change": ctx["rate_contract"][
                        "team_entry_rate_change"
                    ],
                }

        result = explain(
            row["request"], row["context"], Recorded(), "Trusted local explanation."
        )
        assert result["generation_mode"] == "fallback"
        assert result["rejection_reason"] == expected[row["case_id"]]


def test_model_cannot_reference_unselected_turnover_story_or_invent_team_pass_metric():
    import json
    from pathlib import Path

    rows = json.loads(
        (
            Path(__file__).resolve().parents[2]
            / "docs/evaluations/frozen-location-v9.json"
        ).read_text(encoding="utf-8")
    )["rows"]
    row = next(
        r for r in rows if r["policy"] == "single" and r["case_id"] == "location-6407"
    )

    class Recorded:
        def complete(self, *args):
            a = row["answer"]
            c = row["context"]
            return {
                "text": a["text"],
                "evidence_ids": a["model_cited_event_ids"],
                "story_ids": [s["id"] for s in a["narrative_evidence"]],
                "rate_basis": c["rate_contract"]["basis"],
                "team_entry_rate_change": c["rate_contract"]["team_entry_rate_change"],
            }

    answer = explain(
        row["request"], row["context"], Recorded(), "Trusted local explanation."
    )
    assert answer["generation_mode"] == "fallback"
    assert answer["rejection_reason"] == "unapproved_rate_claim"
