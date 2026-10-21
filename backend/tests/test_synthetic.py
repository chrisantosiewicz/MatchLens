from collections import Counter

from matchlens.synthetic import generate_match, generate_seasons


def test_seed_reproducible():
    assert (
        generate_match(7, "shift").model_dump()
        == generate_match(7, "shift").model_dump()
    )
    assert (
        generate_match(8, "shift").model_dump()
        != generate_match(7, "shift").model_dump()
    )


def test_valid_score_and_active_players():
    match = generate_match(7, "shift")
    active = {p.id for p in match.players if p.starter}
    score = Counter()
    for e in match.events:
        if e.event_type == "substitution":
            assert e.player_id in active
            active.remove(e.player_id)
            active.add(e.recipient_id)
        elif e.player_id:
            assert e.player_id in active
        if e.recipient_id and e.event_type == "pass":
            assert e.recipient_id in active
            assert e.recipient_id != e.player_id
        if e.event_type == "shot" and e.outcome == "goal":
            score[e.team_id] += 1
        if e.start:
            assert 0 <= e.start.x <= 105 and 0 <= e.start.y <= 68
    assert dict(score) == match.final_score
    assert len(match.events) > 400
    assert "scenario" not in match.events[0].model_dump()


def test_five_leagues_and_eligible_cohorts():
    seasons = generate_seasons(7)
    assert len({p.league for p in seasons}) == 5
    assert all(
        n >= 30
        for n in Counter(p.position for p in seasons if p.minutes >= 900).values()
    )
    assert {p.id for p in generate_match(7, "shift").players} <= {
        p.player_id for p in seasons
    }
    assert all(s.excludes_current_match for s in seasons)


def test_demo_has_plausible_shot_volume_and_detectable_route_change():
    from matchlens.analytics import compare_windows
    from matchlens.models import Clock

    match = generate_match(7, "shift")
    shots = [e for e in match.events if e.event_type == "shot"]
    assert 8 <= len(shots) <= 45
    assert max(Counter(e.player_id for e in shots).values()) <= 10
    comparison = compare_windows(
        match.events,
        Clock(period=2, elapsed_ms=900000),
        Clock(period=2, elapsed_ms=1500000),
        "north",
    )
    # Realistic failed passes can leave the editorial sample gate unmet.
    assert not comparison["pattern_supported"]
    assert (
        comparison["after"]["routes"]["right"] > comparison["before"]["routes"]["right"]
    )


def test_multiple_seeds_have_balanced_sparse_observations_and_role_limits():
    for seed in range(20):
        complete = generate_match(seed, "null")
        sparse = generate_match(seed, "sparse")
        counts = Counter(
            e.team_id for e in sparse.events if e.event_type != "substitution"
        )
        assert min(counts.values()) / sum(counts.values()) > 0.25
        assert set(counts) == {"north", "harbor"}
        assert len(sparse.events) < len(complete.events) / 2
        passes = [e for e in complete.events if e.event_type == "pass"]
        rate = sum(e.outcome == "complete" for e in passes) / len(passes)
        assert 0.70 <= rate <= 0.94, (seed, rate)
        for record in generate_seasons(seed):
            if record.position == "GK":
                assert record.shots * 90 / record.minutes <= 0.05
