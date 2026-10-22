from fastapi.testclient import TestClient
from matchlens import api
from matchlens.models import Event, Point
from matchlens.store import EventStore
from matchlens.synthetic import generate_match


def test_corrected_event_recomputes_stats_alerts_answers_and_recap(monkeypatch):
    match = generate_match()
    events = [
        Event(
            match_id=match.id,
            event_id=f"pass-{i}",
            sequence=i,
            period=1,
            elapsed_ms=i * 1000,
            team_id="north",
            player_id="north-6",
            recipient_id="north-11",
            event_type="pass",
            outcome="complete",
            possession_id=f"p{i}",
            start=Point(x=40, y=34),
            end=Point(x=60, y=34),
        )
        for i in range(8)
    ]
    match = match.model_copy(update={"events": events})
    store = EventStore()
    for event in events:
        store.upsert(event)
    monkeypatch.setattr(api, "fixtures", lambda: {match.id: match})
    monkeypatch.setattr(api, "event_store", lambda: store, raising=False)
    monkeypatch.setenv("MATCHLENS_INGEST_TOKEN", "test-admin-token")
    monkeypatch.setenv("MATCHLENS_AI_MODE", "template")
    client = TestClient(api.app)
    path = f"/api/matches/{match.id}"
    query = "period=1&elapsed_ms=7000"
    initial = client.get(f"{path}/state?{query}").json()
    assert initial["alerts"][0]["count"] == 8
    version = initial["source_version"]
    assert client.get(f"{path}/revision").json() == {
        "id": match.id,
        "source_version": version,
    }
    assert (
        client.get(f"{path}/state?period=1&elapsed_ms=6000").json()["source_version"]
        == version
    )
    corrected = (
        events[-1]
        .model_copy(update={"revision": 2, "outcome": "incomplete"})
        .model_dump(mode="json")
    )
    assert client.post(f"{path}/events", json=corrected).status_code == 401
    headers = {"X-MatchLens-Token": "test-admin-token"}
    changed = client.post(f"{path}/events", json=corrected, headers=headers)
    assert changed.status_code == 200
    assert changed.json()["invalidated"] == ["pass-7"]
    assert client.get(f"{path}/state?{query}").json()["source_version"] != version
    assert client.get(f"{path}/revision").json()["source_version"] != version
    assert not client.post(f"{path}/events", json=corrected, headers=headers).json()[
        "changed"
    ]
    stats = client.get(f"{path}/players/north-6?{query}").json()["stats"]
    assert stats["pass_attempts"] == 8 and stats["completed_passes"] == 7
    assert all(
        a["count"] != 8 for a in client.get(f"{path}/state?{query}").json()["alerts"]
    )
    answer = client.post(
        f"{path}/questions",
        json={
            "period": 1,
            "elapsed_ms": 7000,
            "player_id": "north-6",
            "question": "How is his passing?",
        },
    ).json()
    assert "7 of 8" in answer["text"]
    assert (
        client.get(f"{path}/recap?{query}&player_id=north-6").json()["stats"][
            "completed_passes"
        ]
        == 7
    )
    assert (
        client.get(f"{path}/players/north-6?period=1&elapsed_ms=6000").json()["stats"][
            "completed_passes"
        ]
        == 7
    )
    store.close()
