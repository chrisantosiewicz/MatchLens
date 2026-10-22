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
                "evidence_ids": [state["context"]["events"][0]["event_id"]],
            }

    p = packet()
    answer = explain(
        {"question": "Why does his passing matter?"}, p, Model(), "Trusted answer."
    )
    assert answer["generation_mode"] == "model"
    assert "limited observation" in answer["text"]

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
    assert p["player_window_minutes"] == {"before": 0, "after": 5}
    assert p["player_rates"]["before"]["actions_per_minute"] is None
    p = context_packet(match, "north-12", Clock(period=2, elapsed_ms=900000), 900000)
    assert p["player_rates"]["after"]["actions_per_minute"] is None
