import pytest
from matchlens.analytics import compare_windows, is_progressive, player_stats
from matchlens.models import Clock, Event, Point
from matchlens.moments import key_moments
from matchlens.profiles import percentile, profile
from matchlens.store import EventStore
from matchlens.synthetic import generate_match, generate_seasons


def entry(i, time, right=True, period=2):
    return Event(
        event_id=str(i),
        period=period,
        elapsed_ms=time,
        team_id="north",
        player_id="north-6",
        recipient_id="north-11",
        event_type="pass",
        outcome="complete",
        possession_id=str(i),
        start=Point(x=80 if right else 25, y=20),
        end=Point(x=92 if right else 13, y=20),
        attack_right=right,
    )


@pytest.mark.parametrize("n", range(1, 11))
def test_comparison_expected_counts_and_provisional(n):
    events = [entry(i, 800_000 + i * 1000) for i in range(n)] + [
        entry(20 + i, 1_000_000 + i * 1000) for i in range(n + 4)
    ]
    result = compare_windows(
        events,
        Clock(period=2, elapsed_ms=1_000_000),
        Clock(period=2, elapsed_ms=1_600_000),
        "north",
    )
    assert result["before"]["box_entries"] == n
    assert result["after"]["box_entries"] == n + 4
    assert result["pattern_supported"] == (n >= 5)
    assert not result["provisional"]
    early = compare_windows(
        events,
        Clock(period=2, elapsed_ms=1_000_000),
        Clock(period=2, elapsed_ms=1_001_000),
        "north",
    )
    assert early["after"]["box_entries"] == 2
    assert early["provisional"]


def test_direction_boundary_and_empty_player():
    e = entry(1, 100, False)
    e.end = Point(x=10, y=20)
    assert is_progressive(e)
    e.end = Point(x=15, y=20)
    # Distance to goal includes lateral displacement, so horizontal 10m alone is not sufficient.
    assert not is_progressive(e)
    assert (
        player_stats([], "north-6", Clock(period=1, elapsed_ms=0))["pass_completion"]
        is None
    )
    result = compare_windows(
        [entry(1, 0, False)],
        Clock(period=2, elapsed_ms=0),
        Clock(period=2, elapsed_ms=1),
        "north",
    )
    assert result["before"]["box_entries"] == 0
    assert result["after"]["box_entries"] == 1
    assert not result["pattern_supported"]


def test_store_duplicate_revision_restart(tmp_path):
    path = tmp_path / "events.sqlite"
    store = EventStore(path)
    e = entry(1, 100)
    assert store.upsert(e)["changed"]
    assert not store.upsert(e)["changed"]
    updated = e.model_copy(update={"revision": 2, "outcome": "incomplete"})
    assert store.upsert(updated)["invalidated"] == [e.event_id]
    assert not store.upsert(e)["changed"]
    store.close()
    restarted = EventStore(path)
    assert restarted.events_at(2, 100)[0].outcome == "incomplete"
    assert restarted.events_at(2, 99) == []
    restarted.close()


def test_percentiles_and_eligibility():
    assert percentile(2, [1, 2, 2, 4]) == 50
    seasons = generate_seasons()
    p = profile("north-6", seasons)
    assert p["cohort_size"] >= 30
    assert all(0 <= m["percentile"] <= 100 for m in p["metrics"])
    small = [s for s in seasons if s.player_id == "north-6"]
    assert profile("north-6", small)["metrics"][0]["percentile"] is None
    small[0].minutes = 899
    assert profile("north-6", small)["cohort_size"] == 0


def test_key_moments_evidence_and_future_exclusion():
    events = [
        entry(1, 100),
        Event(
            event_id="shot",
            period=2,
            elapsed_ms=200,
            team_id="north",
            player_id="north-11",
            event_type="shot",
            outcome="goal",
            possession_id="1",
            start=Point(x=92, y=20),
        ),
    ]
    assert key_moments(events, "north-6", Clock(period=2, elapsed_ms=150)) == []
    moments = key_moments(events, "north-6", Clock(period=2, elapsed_ms=200))
    assert len(moments) == 1
    assert set(moments[0]["evidence_ids"]) == {"1", "shot"}
    assert key_moments(events, "unknown", Clock(period=2, elapsed_ms=200)) == []
    match = generate_match()
    assert (
        len(key_moments(match.events, "north-6", Clock(period=2, elapsed_ms=2_700_000)))
        <= 5
    )


def test_moment_does_not_attribute_actions_after_shot():
    shot = Event(
        event_id="shot",
        sequence=1,
        period=2,
        elapsed_ms=100,
        team_id="north",
        player_id="north-11",
        event_type="shot",
        outcome="saved",
        possession_id="p",
    )
    later = entry(2, 100).model_copy(update={"possession_id": "p", "sequence": 2})
    moments = key_moments([shot, later], "north-6", Clock(period=2, elapsed_ms=200))
    assert moments == []
    assert (
        key_moments([shot], "north-11", Clock(period=2, elapsed_ms=200))[0]["title"]
        == "Attempted a shot"
    )


def test_turnover_followed_by_opponent_shot_is_temporal_moment():
    turnover = Event(
        event_id="loss",
        period=2,
        elapsed_ms=1000,
        team_id="north",
        player_id="north-6",
        event_type="turnover",
        possession_id="p",
    )
    shot = Event(
        event_id="opp-shot",
        period=2,
        elapsed_ms=15000,
        team_id="harbor",
        player_id="harbor-11",
        event_type="shot",
        outcome="saved",
        possession_id="opp",
    )
    assert (
        key_moments([turnover, shot], "north-6", Clock(period=2, elapsed_ms=10000))
        == []
    )
    moment = key_moments(
        [turnover, shot], "north-6", Clock(period=2, elapsed_ms=20000)
    )[0]
    assert moment["title"] == "Turnover followed by an opposition shot"
    assert moment["evidence_ids"] == ["loss", "opp-shot"]


def test_zero_duration_window_contains_no_actions_at_anchor():
    clock = Clock(period=2, elapsed_ms=1000)
    result = compare_windows([entry(1, 1000)], clock, clock, "north")
    assert result["after"]["duration_ms"] == 0
    assert result["after"]["actions"] == 0
    assert result["after"]["box_entries"] == 0
    assert result["after"]["evidence_ids"] == []


def test_unequal_windows_compare_event_frequency_not_raw_totals():
    events = [entry(i, 400000 + i * 10000) for i in range(4)] + [
        entry(10 + i, 1000000 + i * 10000) for i in range(2)
    ]
    result = compare_windows(
        events,
        Clock(period=2, elapsed_ms=900000),
        Clock(period=2, elapsed_ms=1200000),
        "north",
    )
    assert result["before"]["box_entries_per_minute"] == 0.4
    assert result["after"]["box_entries_per_minute"] == 0.4
    assert result["entry_rate_change"] == "unchanged"
    zero = compare_windows(
        events,
        Clock(period=2, elapsed_ms=900000),
        Clock(period=2, elapsed_ms=900000),
        "north",
    )
    assert zero["after"]["box_entries_per_minute"] is None
    assert zero["entry_rate_change"] == "not_comparable"
