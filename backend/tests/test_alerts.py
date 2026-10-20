from matchlens.alerts import progressive_alerts
from matchlens.models import Clock, Event, Player, Point


def test_eighth_pass_alert_has_correct_runner_up_and_no_future_events():
    players = [
        Player(id="n", name="Nico Vega", team_id="north", number=12, position="CM"),
        Player(id="l", name="Leon Fischer", team_id="harbor", number=8, position="CM"),
    ]
    events = []
    for i in range(5):
        events.append(
            Event(
                event_id=f"l{i}",
                sequence=i,
                period=1,
                elapsed_ms=i * 1000,
                team_id="harbor",
                player_id="l",
                event_type="pass",
                outcome="complete",
                possession_id=str(i),
                start=Point(x=40, y=34),
                end=Point(x=60, y=34),
            )
        )
    for i in range(8):
        events.append(
            Event(
                event_id=f"n{i}",
                sequence=10 + i,
                period=1,
                elapsed_ms=10000 + i * 1000,
                team_id="north",
                player_id="n",
                event_type="pass",
                outcome="complete",
                possession_id=str(i),
                start=Point(x=40, y=34),
                end=Point(x=60, y=34),
            )
        )
    before = progressive_alerts(events, players, Clock(period=1, elapsed_ms=16999))
    assert not any(a["count"] == 8 for a in before)
    alert = progressive_alerts(events, players, Clock(period=1, elapsed_ms=17000))[-1]
    assert alert["player_id"] == "n" and alert["count"] == 8
    assert alert["runner_up"]["name"] == "Leon Fischer"
    assert alert["runner_up"]["rank"] == 2
    assert alert["runner_up"]["count"] == 5
    assert progressive_alerts(events, players, Clock(period=1, elapsed_ms=50000)) == []
