from copy import deepcopy
from math import hypot

from matchlens.models import Clock
from matchlens.synthetic import generate_match


def test_corner_scenario_has_reproducible_explicit_positional_evidence():
    match = generate_match(7, "corners")
    assert match == generate_match(7, "corners")
    assert match != generate_match(8, "corners")
    assert len(match.position_frames) == 12
    deliveries = [
        e for e in match.events if e.set_piece and e.set_piece.phase == "delivery"
    ]
    assert len(deliveries) == 3
    assert len(match.events) > 400
    assert not generate_match(7, "null").position_frames


def test_corner_counts_are_synchronized_and_follow_active_roster_across_seeds():
    from matchlens.set_pieces import corner_context

    for seed in range(20):
        match = generate_match(seed, "corners")
        result = corner_context(match, Clock(period=2, elapsed_ms=1500000))
        assert len(result["corners"]) == 3
        players = {p.id: p for p in match.players}
        for corner in result["corners"]:
            assert corner["frames"][1]["counts"] == {
                "attackers": 5,
                "defenders": 8,
                "defending_goalkeepers": 1,
            }
            assert corner["first_contact"]["player_id"] in players
            for frame in corner["frames"]:
                assert frame["available"] and len(frame["positions"]) == 22
                assert len({p["player_id"] for p in frame["positions"]}) == 22
                assert all(
                    0 <= p["point"]["x"] <= 105 and 0 <= p["point"]["y"] <= 68
                    for p in frame["positions"]
                )
                if frame["period"] == 2:
                    assert "north-9" not in {p["player_id"] for p in frame["positions"]}
                    assert "north-12" in {p["player_id"] for p in frame["positions"]}
            for before, after in zip(corner["frames"], corner["frames"][1:]):
                old = {p["player_id"]: p["point"] for p in before["positions"]}
                dt = (after["elapsed_ms"] - before["elapsed_ms"]) / 1000
                assert all(
                    hypot(
                        p["point"]["x"] - old[p["player_id"]]["x"],
                        p["point"]["y"] - old[p["player_id"]]["y"],
                    )
                    / dt
                    < 9
                    for p in after["positions"]
                )
        assert all(
            players[e.player_id].position != "GK"
            for e in match.events
            if e.set_piece
            and e.player_id
            and e.event_type in {"shot", "pass"}
            and e.set_piece.phase == "delivery"
        )


def test_clock_reveals_only_observed_phases_and_old_feeds_have_no_positions():
    from matchlens.set_pieces import corner_context

    match = generate_match(7, "corners")
    assert not corner_context(match, Clock(period=1, elapsed_ms=1200000))["corners"]
    setup = corner_context(match, Clock(period=1, elapsed_ms=1201000))["corners"][0]
    assert [f["phase"] for f in setup["frames"]] == ["setup"]
    assert setup["first_contact"] is None and setup["outcome"] is None
    delivery = corner_context(match, Clock(period=1, elapsed_ms=1204000))["corners"][0]
    assert delivery["first_contact"] is None and delivery["outcome"] is None
    assert not corner_context(
        generate_match(7, "shift"), Clock(period=2, elapsed_ms=1500000)
    )["available"]


def test_missing_stale_or_inactive_player_positions_withhold_counts():
    from matchlens.set_pieces import corner_context

    original = generate_match(7, "corners")
    for defect in ["missing", "duplicate", "inactive", "stale", "clock"]:
        match = deepcopy(original)
        frame = match.position_frames[1]
        if defect == "missing":
            frame.positions.pop()
        elif defect == "duplicate":
            frame.positions[-1].player_id = frame.positions[0].player_id
        elif defect == "inactive":
            frame.positions[-1].player_id = "north-13"
        elif defect == "stale":
            next(
                e for e in match.events if e.event_id == frame.anchor_event_id
            ).revision += 1
        else:
            frame.elapsed_ms += 1
        row = corner_context(match, Clock(period=1, elapsed_ms=1212000))["corners"][0]
        delivery = next(f for f in row["frames"] if f["phase"] == "delivery")
        assert not delivery["available"] and delivery["counts"] is None
        assert not delivery["positions"]
        assert "five" not in row["text"].lower()


def test_counting_mirrors_direction_and_includes_penalty_area_boundary():
    from matchlens.set_pieces import box_occupancy

    match = generate_match(7, "corners")
    players = {p.id: p for p in match.players}
    frame = match.position_frames[1]
    entries = [p.model_dump() for p in frame.positions]
    # Manually set exactly two known attackers inside/on the boundary.
    for p in entries:
        p["point"] = {"x": 50, "y": 34}
    entries[0]["point"] = {"x": 88.5, "y": 13.84}
    entries[1]["point"] = {"x": 100, "y": 54.16}
    assert box_occupancy(entries, players, "north", True)["attackers"] == 2
    flipped = [
        {**p, "point": {"x": 105 - p["point"]["x"], "y": 68 - p["point"]["y"]}}
        for p in entries
    ]
    assert box_occupancy(flipped, players, "north", False)["attackers"] == 2


def test_corner_source_version_changes_with_positional_correction():
    from matchlens.api import source_version

    match = generate_match(7, "corners")
    before = source_version(match)
    match.position_frames[1].positions[0].point.x += 1
    assert source_version(match) != before


def test_corner_api_and_questions_preserve_clock_and_source(monkeypatch):
    from fastapi.testclient import TestClient
    from matchlens import api

    monkeypatch.setenv("MATCHLENS_AI_MODE", "template")
    client = TestClient(api.app)
    assert any(m["id"].endswith("corners") for m in client.get("/api/matches").json())
    result = client.get(
        "/api/matches/match-7-corners/set-pieces?period=1&elapsed_ms=1204000"
    )
    assert result.status_code == 200
    data = result.json()
    assert data["corners"][0]["first_contact"] is None
    answer = client.post(
        "/api/matches/match-7-corners/questions",
        json={
            "period": 1,
            "elapsed_ms": 1204000,
            "player_id": "north-6",
            "question": "Who was in the box for the corner?",
            "anchor_ms": 0,
        },
    )
    assert answer.status_code == 200
    assert answer.json()["source_version"] == data["source_version"]
    assert answer.json()["generation_mode"] == "template"
    assert "5 attackers" in answer.json()["text"]
    assert "wide" not in answer.json()["text"]
    assert answer.json()["position_frame_ids"]


def test_spanish_corner_summary_names_first_contact_and_outcome_without_intention():
    from matchlens.set_pieces import corner_context

    match = generate_match(7, "corners")
    corner = corner_context(match, Clock(period=2, elapsed_ms=1212000), "es")[
        "corners"
    ][-1]
    assert "área" in corner["text"] and "contacto" in corner["text"]
    assert "intención" in corner["limitation"]
    assert corner["evidence_ids"] and corner["position_frame_ids"]


def test_corner_question_handles_an_inactive_selected_substitute():
    from matchlens.set_pieces import corner_answer

    result = corner_answer(
        generate_match(7, "corners"),
        {"period": 2, "elapsed_ms": 1500000, "player_id": "north-13", "language": "en"},
    )
    assert "No delivery position is recorded for Sami Morel" in result["text"]
    assert "outside the box" not in result["text"]


def test_goalkeeper_outside_the_box_is_not_claimed_inside():
    from matchlens.set_pieces import corner_context

    match = generate_match(7, "corners")
    frame = match.position_frames[1]
    next(p for p in frame.positions if p.player_id == "harbor-1").point.x = 80
    row = corner_context(match, Clock(period=1, elapsed_ms=1212000))["corners"][0]
    assert "7 defenders" in row["text"]
    assert "0 goalkeepers" in row["text"]


def test_corrected_malformed_phase_is_withheld_instead_of_crashing_or_inventing_contact():
    from matchlens.set_pieces import corner_context

    match = generate_match(7, "corners")
    event = next(
        e for e in match.events if e.set_piece and e.set_piece.phase == "outcome"
    )
    event.player_id = None
    event.revision += 1
    row = corner_context(match, Clock(period=1, elapsed_ms=1212000))["corners"][0]
    assert row["outcome"] is None
    assert "wide" not in row["text"] and "saved" not in row["text"]


def test_substitution_between_snapshots_does_not_invent_a_run_or_crash():
    from matchlens.models import Event
    from matchlens.set_pieces import corner_context

    match = generate_match(7, "corners")
    match.events.append(
        Event(
            match_id=match.id,
            event_id="test-sub",
            period=1,
            elapsed_ms=1202000,
            team_id="north",
            player_id="north-9",
            recipient_id="north-12",
            event_type="substitution",
            possession_id="test-sub",
        )
    )
    delivery = next(
        e
        for e in match.events
        if e.event_id == match.position_frames[1].anchor_event_id
    )
    delivery.player_id = "north-12"
    delivery.revision += 1
    for frame in match.position_frames[1:4]:
        next(
            p for p in frame.positions if p.player_id == "north-9"
        ).player_id = "north-12"
        if frame.anchor_event_id == delivery.event_id:
            frame.anchor_event_revision = delivery.revision
    row = corner_context(match, Clock(period=1, elapsed_ms=1212000))["corners"][0]
    assert row["frames"][1]["available"]
    assert "north-12" not in row["entered_box_ids"]


def test_incomplete_followup_pass_is_not_narrated_as_complete():
    from matchlens.set_pieces import corner_context

    match = generate_match(7, "corners")
    event = next(
        e
        for e in match.events
        if e.event_id == match.position_frames[3].anchor_event_id
    )
    event.event_type = "pass"
    event.outcome = "incomplete"
    event.recipient_id = "north-4"
    event.revision += 1
    row = corner_context(match, Clock(period=1, elapsed_ms=1212000))["corners"][0]
    assert "completes a pass" not in row["text"]
    assert "incomplete" in row["text"]


def test_invalid_or_out_of_order_contact_cannot_be_reported_as_first_contact():
    from matchlens.set_pieces import corner_context

    for defect in ["inactive", "wrong_kind", "order", "duplicate"]:
        match = generate_match(7, "corners")
        contact = next(
            e
            for e in match.events
            if e.event_id == match.position_frames[2].anchor_event_id
        )
        if defect == "inactive":
            contact.player_id = "north-13"
        elif defect == "wrong_kind":
            contact.event_type = "stoppage"
        elif defect == "order":
            contact.elapsed_ms = 1202000
        else:
            match.events.append(
                contact.model_copy(update={"event_id": "duplicate-contact"})
            )
        contact.revision += 1
        row = corner_context(match, Clock(period=1, elapsed_ms=1212000))["corners"][0]
        assert row["first_contact"] is None and row["outcome"] is None
        assert all(not f["available"] for f in row["frames"])


def test_recap_includes_only_visible_corner_context_and_positional_sources():
    from matchlens.summaries import build_recap

    match = generate_match(7, "corners")
    before = build_recap(match, "north-6", Clock(period=1, elapsed_ms=1200000), "en")
    assert not before.get("position_frame_ids")
    after = build_recap(match, "north-6", Clock(period=1, elapsed_ms=1204000), "en")
    assert "5 attackers" in after["text"] and after["position_frame_ids"]
    assert "20:11" not in after["text"]


def test_ordinary_questions_and_guide_share_positional_source_identity(monkeypatch):
    from fastapi.testclient import TestClient
    from matchlens import api

    monkeypatch.setenv("MATCHLENS_AI_MODE", "template")
    monkeypatch.setenv("MATCHLENS_AI_POLICY", "canonical_single")
    client = TestClient(api.app, raise_server_exceptions=False)
    payload = {
        "period": 2,
        "elapsed_ms": 1570000,
        "player_id": "north-6",
        "anchor_ms": 900000,
        "language": "en",
    }
    version = client.get("/api/matches/match-7-corners/revision").json()[
        "source_version"
    ]
    for question in [
        "Did his passing cause the goal?",
        "Why does his passing matter?",
        "How involved has he been?",
    ]:
        response = client.post(
            "/api/matches/match-7-corners/questions",
            json={**payload, "question": question},
        )
        assert response.status_code == 200, response.text
        assert response.json()["source_version"] == version
    guide = client.post(
        "/api/matches/match-7-corners/guidance",
        json={
            **payload,
            "question": "Why does his passing matter?",
            "branch": "attacking",
            "expected_source_version": version,
        },
    )
    assert guide.status_code == 200
    assert guide.json()["source_version"] == version and guide.json()["cards"]
