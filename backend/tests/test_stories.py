from matchlens.models import Clock, Event, MatchFixture, Player
from matchlens.stories import sequence_stories


def fixture():
    def event(
        id, time, player, kind, outcome="complete", possession="a", team="home", **kw
    ):
        return Event(
            event_id=id,
            period=2,
            elapsed_ms=time,
            sequence=time,
            team_id=team,
            player_id=player,
            event_type=kind,
            outcome=outcome,
            possession_id=possession,
            **kw,
        )

    return MatchFixture(
        id="test",
        teams={"home": "Home", "away": "Away"},
        final_score={"home": 0, "away": 0},
        players=[
            Player(id="p", name="Alex", team_id="home", number=6, position="CM"),
            Player(id="b", name="Blair", team_id="home", number=9, position="ST"),
        ],
        events=[
            event(
                "link",
                1000,
                "p",
                "pass",
                recipient_id="b",
                start={"x": 40, "y": 34},
                end={"x": 43, "y": 34},
            ),
            event("shot", 6000, "b", "shot", "saved"),
            event(
                "forward",
                11000,
                "p",
                "pass",
                possession="b",
                recipient_id="b",
                start={"x": 40, "y": 34},
                end={"x": 60, "y": 34},
            ),
            event("loss", 16000, "b", "turnover", "recorded", possession="b"),
        ],
    )


def test_build_up_explains_non_progressive_contribution_with_exact_sequence():
    stories = sequence_stories(fixture(), "p", Clock(period=2, elapsed_ms=20000))
    s = next(s for s in stories if s["kind"] == "shot_build_up")
    assert s["evidence_ids"] == ["link", "shot"]
    assert s["player_action_progressive"] is False
    assert s["outcome"] == "saved"
    assert "assist" in s["limitation_en"] and "headline" in s["meaning_en"]


def test_progression_without_shot_requires_observed_end_and_never_peeks_ahead():
    match = fixture()
    early = sequence_stories(match, "p", Clock(period=2, elapsed_ms=12000))
    assert not any(s["kind"] == "progression_without_shot" for s in early)
    late = sequence_stories(match, "p", Clock(period=2, elapsed_ms=20000))
    s = next(s for s in late if s["kind"] == "progression_without_shot")
    assert s["evidence_ids"] == ["forward", "loss"]
    assert s["outcome"] == "turnover"
    assert not sequence_stories(
        match.model_copy(update={"feed_completeness": "incomplete"}),
        "p",
        Clock(period=2, elapsed_ms=20000),
    )


def test_opponent_same_possession_id_cannot_turn_a_pass_into_build_up_credit():
    match = fixture()
    match.events[1] = match.events[1].model_copy(update={"team_id": "away"})
    assert not any(
        s["kind"] == "shot_build_up"
        for s in sequence_stories(match, "p", Clock(period=2, elapsed_ms=9000))
    )


def test_turnover_story_stops_when_own_possession_is_observed_again():
    match = fixture()
    match.events = [
        Event(
            event_id="loss",
            period=2,
            elapsed_ms=1000,
            team_id="home",
            player_id="p",
            event_type="turnover",
            possession_id="a",
        ),
        Event(
            event_id="regain-pass",
            period=2,
            elapsed_ms=2000,
            team_id="home",
            player_id="b",
            event_type="pass",
            outcome="complete",
            possession_id="b",
        ),
        Event(
            event_id="opp-shot",
            period=2,
            elapsed_ms=5000,
            team_id="away",
            player_id="opponent",
            event_type="shot",
            outcome="wide",
            possession_id="c",
        ),
    ]
    assert not sequence_stories(match, "p", Clock(period=2, elapsed_ms=6000))
