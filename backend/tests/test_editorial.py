from matchlens.editorial import (
    action_location,
    entry_possessions,
    game_state_context,
    passing_context,
    same_metric_contrast,
)
from matchlens.models import Clock, Event
from test_stories import fixture


def ev(
    id,
    ms,
    kind="pass",
    player="p",
    team="home",
    possession="a",
    outcome="complete",
    start=None,
    end=None,
    recipient="b",
):
    return Event(
        event_id=id,
        period=2,
        elapsed_ms=ms,
        sequence=ms,
        team_id=team,
        player_id=player,
        event_type=kind,
        outcome=outcome,
        possession_id=possession,
        start=start,
        end=end,
        recipient_id=recipient,
    )


def test_location_flips_attack_direction_and_distinguishes_backward_from_progressive():
    e = ev("pass", 1000, start={"x": 25, "y": 34}, end={"x": 15, "y": 34})
    m = Event.model_validate(
        {
            **e.model_dump(),
            "attack_right": False,
            "start": {"x": 80, "y": 34},
            "end": {"x": 90, "y": 34},
        }
    )
    assert action_location(e) == action_location(m)
    assert action_location(e)["direction"] == "backward"
    assert action_location(e)["origin_zone"] == "defensive third"
    assert action_location(e)["longitudinal_gain_m"] == -10
    assert action_location(ev("missing", 1))["available"] is False


def test_backward_circulation_requires_locations_and_remains_descriptive():
    m = fixture()
    m.events = [
        ev(
            str(i),
            1000 * i,
            start={"x": 40, "y": 34},
            end={"x": 25, "y": 34},
            possession=str(i),
        )
        for i in range(1, 6)
    ]
    report = passing_context(m, "p", Clock(period=2, elapsed_ms=10000), 0)
    assert report["backward_completed"] == 5 and report["recycling_eligible"]
    assert report["evidence_ids"] == ["1", "2", "3", "4", "5"]
    assert "tempo" in report["prohibited_inferences"]
    assert not passing_context(
        m.model_copy(update={"feed_completeness": "incomplete"}),
        "p",
        Clock(period=2, elapsed_ms=10000),
        0,
    )["recycling_eligible"]


def test_box_access_counts_completed_possessions_once_and_excludes_open_sequence():
    m = fixture()
    events = []
    for i in range(9):
        t = 10000 * i + 1000
        events += [
            ev(
                f"entry-{i}",
                t,
                possession=str(i),
                start={"x": 80, "y": 34},
                end={"x": 95, "y": 34},
            ),
            ev(
                f"reentry-{i}",
                t + 100,
                possession=str(i),
                start={"x": 80, "y": 34},
                end={"x": 95, "y": 34},
            ),
        ]
        if i < 8:
            events.append(
                ev(
                    f"end-{i}",
                    t + 200,
                    kind="shot" if i == 0 else "turnover",
                    possession=str(i),
                    outcome="wide" if i == 0 else "recorded",
                )
            )
    m.events = events
    report = entry_possessions(m, "home", Clock(period=2, elapsed_ms=90000))
    assert report["completed_entry_possessions"] == 8
    assert report["with_later_shot"] == 1 and report["unfinished_excluded"] == 1
    assert report["spotlight_eligible"] is True
    assert not entry_possessions(
        m.model_copy(update={"feed_completeness": "incomplete"}),
        "home",
        Clock(period=2, elapsed_ms=90000),
    )["spotlight_eligible"]


def test_contrast_requires_same_metric_full_exposure_and_nontrivial_counts():
    assert not same_metric_contrast(1, 2, 8, 5, 10, 10, 10, 10, True)["eligible"]
    r = same_metric_contrast(5, 2, 5, 9, 10, 10, 10, 10, True)
    assert r["eligible"] and r["metric"] == "box_entries"
    assert r["player_before_rate"] == 0.5 and r["player_after_rate"] == 0.2
    assert not same_metric_contrast(5, 2, 5, 9, 10, 10, 0, 10, True)["eligible"]
    assert not same_metric_contrast(5, 2, 5, 9, 10, 5, 10, 5, True)["eligible"]


def test_late_game_state_uses_visible_goals_not_fixture_final_result():
    m = fixture()
    m.events = [
        ev("goal", 1000, kind="shot", outcome="goal"),
        ev("future", 2500000, kind="shot", team="away", outcome="goal"),
    ]
    r = game_state_context(m, "home", Clock(period=2, elapsed_ms=2400000))
    assert (
        r["phase"] == "late"
        and r["state"] == "leading"
        and r["score_for"] == 1
        and r["score_against"] == 0
    )
    assert (
        game_state_context(
            m.model_copy(update={"feed_completeness": "incomplete"}),
            "home",
            Clock(period=2, elapsed_ms=2400000),
        )["available"]
        is False
    )


from matchlens.stories import sequence_stories


def test_third_pass_credit_keeps_location_but_not_line_break_claim():
    m = fixture()
    m.events = [
        ev("long", 1000, start={"x": 25, "y": 34}, end={"x": 80, "y": 34}),
        ev("drop", 5000, player="b", recipient="c"),
        ev("layoff", 9000, player="c", recipient="b"),
        ev("shot", 12000, kind="shot", player="b", outcome="goal"),
    ]
    story = next(
        s
        for s in sequence_stories(m, "p", Clock(period=2, elapsed_ms=15000))
        if s["kind"] == "shot_build_up"
    )
    assert story["pass_rank_before_shot"] == 3
    assert story["action_location"]["own_half_to_final_third"]
    assert story["action_location"]["distance_m"] == 55
    assert "line break" in story["prohibited_inferences"]
    m.events.insert(3, ev("extra", 10000, player="b", recipient="c"))
    m.events[-1] = m.events[-1].model_copy(update={"player_id": "c"})
    assert not any(
        s["kind"] == "shot_build_up"
        for s in sequence_stories(m, "p", Clock(period=2, elapsed_ms=15000))
    )


def test_recovery_spotlight_requires_box_entry_or_shot_inside_action_and_time_caps():
    m = fixture()
    m.events = [
        ev("recover", 1000, kind="recovery", outcome="recorded"),
        ev("pass", 4000, player="b"),
        ev("entry", 7000, player="b", start={"x": 80, "y": 34}, end={"x": 95, "y": 34}),
        ev("shot", 10000, kind="shot", player="b", outcome="saved"),
    ]
    story = next(
        s
        for s in sequence_stories(m, "p", Clock(period=2, elapsed_ms=15000))
        if s["kind"] == "recovery_followed_by_attack"
    )
    assert story["sequence_duration_seconds"] == 9
    assert story["subsequent_on_ball_actions"] == 3
    assert story["evidence_ids"] == ["recover", "pass", "entry", "shot"]
    m.events = [m.events[0], m.events[1]]
    assert not sequence_stories(m, "p", Clock(period=2, elapsed_ms=15000))


def test_fast_turnover_shot_records_area_and_intervening_actions_without_blame():
    m = fixture()
    m.events = [
        ev("loss", 1000, kind="turnover", outcome="recorded", start={"x": 20, "y": 34}),
        ev("opp-pass", 3000, player="op", team="away", possession="b"),
        ev(
            "shot",
            6000,
            kind="shot",
            player="op",
            team="away",
            possession="b",
            outcome="wide",
        ),
    ]
    story = next(
        s
        for s in sequence_stories(m, "p", Clock(period=2, elapsed_ms=9000))
        if s["kind"] == "turnover_then_opposition_shot"
    )
    assert story["immediate_attempt"] and story["intervening_on_ball_actions"] == 1
    assert story["action_location"]["origin_zone"] == "defensive third"
    assert "sole blame" in story["prohibited_inferences"]


def test_ineligible_editorial_conclusions_are_removed_from_model_input():
    from matchlens.explainer import context_packet, model_context
    from matchlens.synthetic import generate_match

    p = context_packet(
        generate_match(7, "shift"),
        "north-6",
        Clock(period=2, elapsed_ms=1200000),
        900000,
    )
    model = model_context(p)
    assert "player_progressive_passes" not in model
    assert model["editorial_context"]["player_team_contrast"]["eligible"] is False
    assert (
        "player_before_count" not in model["editorial_context"]["player_team_contrast"]
    )
    assert (
        model["editorial_context"]["source_revision"]
        == p["editorial_context"]["source_revision"]
    )


def test_same_conclusion_and_sources_for_fan_and_analyst_editorial_summary():
    from matchlens.api import Question, template_question
    from matchlens.synthetic import generate_match

    m = generate_match(7, "shift")
    fan = template_question(
        m.id,
        Question(
            period=2,
            elapsed_ms=1500000,
            player_id="north-6",
            question="Why does his passing matter?",
        ),
        m,
    )
    analyst = template_question(
        m.id,
        Question(
            period=2,
            elapsed_ms=1500000,
            player_id="north-6",
            question="Why does his passing matter?",
            depth="analyst",
        ),
        m,
    )
    assert fan["editorial_context"] == analyst["editorial_context"]
    assert fan["narrative_evidence"] == analyst["narrative_evidence"]
    assert fan["evidence_ids"] == analyst["evidence_ids"]
    assert fan["editorial_context"]["source_revision"] == fan["source_version"]


def test_rendered_player_team_contrast_includes_teammate_entry_sources():
    from matchlens.api import Question, template_question

    m = fixture()
    m.events = []
    for i in range(5):
        m.events.append(
            ev(
                f"before-{i}",
                1000 + i * 100000,
                possession=f"b{i}",
                start={"x": 80, "y": 34},
                end={"x": 95, "y": 34},
            )
        )
    for i in range(9):
        m.events.append(
            ev(
                f"after-{i}",
                601000 + i * 60000,
                player="p" if i < 2 else "b",
                possession=f"a{i}",
                start={"x": 80, "y": 34},
                end={"x": 95, "y": 34},
            )
        )
    answer = template_question(
        m.id,
        Question(
            period=2,
            elapsed_ms=1200000,
            anchor_ms=600000,
            player_id="p",
            question="What changed since the selected moment?",
        ),
        m,
    )
    assert answer["editorial_context"]["player_team_contrast"]["eligible"]
    assert "after-8" in answer["evidence_ids"]


def test_recovery_card_names_box_entry_even_without_a_later_shot():
    m = fixture()
    m.events = [
        ev("recover", 1000, kind="recovery", outcome="recorded"),
        ev("entry", 4000, player="b", start={"x": 80, "y": 34}, end={"x": 95, "y": 34}),
    ]
    story = next(
        s
        for s in sequence_stories(m, "p", Clock(period=2, elapsed_ms=5000))
        if s["kind"] == "recovery_followed_by_attack"
    )
    assert story["qualifying_outcome"] == "box entry"
    assert story["review_window_seconds"] == 20
