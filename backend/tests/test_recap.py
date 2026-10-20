from matchlens.models import Clock, Event, MatchFixture, Player
from matchlens.summaries import build_recap


def fixture():
    players = [
        Player(id="n6", name="Mateo Silva", team_id="north", number=6, position="CM"),
        Player(id="h9", name="Nico Vega", team_id="harbor", number=9, position="ST"),
    ]
    events = [
        Event(
            event_id="p",
            period=2,
            elapsed_ms=1000,
            team_id="north",
            player_id="n6",
            event_type="pass",
            outcome="complete",
            possession_id="p1",
        ),
        Event(
            event_id="g",
            period=2,
            elapsed_ms=592000,
            team_id="harbor",
            player_id="h9",
            event_type="shot",
            outcome="goal",
            possession_id="p2",
        ),
    ]
    return MatchFixture(
        id="demo",
        teams={"north": "Northbridge FC", "harbor": "Harbor Athletic"},
        players=players,
        events=events,
        final_score={"harbor": 1},
    )


def test_recap_names_exact_clock_goal_and_non_involvement():
    recap = build_recap(fixture(), "n6", Clock(period=2, elapsed_ms=592000), "en")
    assert "At your selected time: 54:52" in recap["text"]
    assert "54:52" in recap["text"] and "Nico Vega scored" in recap["text"]
    assert "Mateo Silva was not involved in the recorded goal sequence" in recap["text"]
    assert "completed 1 pass" in recap["text"]
    assert "no key recorded moments yet" in recap["text"]
    assert recap["moment_count"] == 0
    assert "g" in recap["evidence_ids"]


def test_recap_before_goal_has_no_future_scorer_and_spanish_clock():
    result = build_recap(fixture(), "n6", Clock(period=2, elapsed_ms=590000), "en")
    assert "Nico Vega" not in result["text"]
    assert result["score"] == {"north": 0, "harbor": 0}
    assert "54:50" in result["text"]
    spanish = build_recap(fixture(), "h9", Clock(period=2, elapsed_ms=592000), "es")
    assert "54:52" in spanish["text"]
    assert spanish["moment_count"] == 1
    assert "participó" in spanish["text"]
