from fastapi.testclient import TestClient
from matchlens.api import app

client = TestClient(app)


def test_player_and_clock_contracts():
    matches = client.get("/api/matches").json()
    match = matches[0]["id"]
    state = client.get(f"/api/matches/{match}/state?period=2&elapsed_ms=1200000").json()
    assert all((e["period"], e["elapsed_ms"]) <= (2, 1200000) for e in state["events"])
    player = client.get(
        f"/api/matches/{match}/players/north-6?period=2&elapsed_ms=1200000"
    ).json()
    assert player["profile"]["synthetic"]
    assert len(player["moments"]) <= 5
    assert (
        client.get(
            f"/api/matches/{match}/players/north-13?period=1&elapsed_ms=0"
        ).json()["stats"]["actions"]
        == 0
    )
    assert client.get(f"/api/matches/{match}/players/unknown").status_code == 404
    assert client.get(f"/api/matches/{match}/state?period=3").status_code == 422
    assert client.get("/api/matches/unknown/state").status_code == 404
    assert (
        client.get(
            f"/api/matches/{match}/comparison?period=2&anchor_ms=2000000&elapsed_ms=1000000"
        ).status_code
        == 422
    )


def test_stat_questions_and_recap_are_clock_safe():
    match = client.get("/api/matches").json()[0]["id"]
    payload = {
        "period": 2,
        "elapsed_ms": 1200000,
        "player_id": "north-6",
        "question": "How involved has he been?",
        "language": "en",
        "depth": "analyst",
    }
    response = client.post(f"/api/matches/{match}/questions", json=payload)
    assert response.status_code == 200
    story = response.json()
    assert story["generation_mode"] == "template"
    assert story["evidence_ids"]
    assert (
        "tracking"
        in client.post(
            f"/api/matches/{match}/questions",
            json={**payload, "question": "How fast is he running?"},
        )
        .json()["text"]
        .lower()
    )
    recap = client.get(f"/api/matches/{match}/recap?period=1&elapsed_ms=0").json()
    assert recap["score"] == {"north": 0, "harbor": 0}
    assert "synthetic" in client.get("/api/health").json()["data_mode"]


def test_configured_workflow_is_used_for_player_answers(monkeypatch):
    monkeypatch.setenv("MATCHLENS_AI_POLICY", "specialist")
    import matchlens.api as api_module

    class Provider:
        def complete(self, role, state):
            if role == "analyst":
                return {"tool": "requested_answer"}
            if role == "reviewer":
                return {"verdict": "accept"}
            return {"fact_ids": [state["facts"][0]["id"]]}

    monkeypatch.setattr(
        api_module, "configured_provider", lambda: Provider(), raising=False
    )
    match = client.get("/api/matches").json()[0]["id"]
    answer = client.post(
        f"/api/matches/{match}/questions",
        json={
            "period": 2,
            "elapsed_ms": 1200000,
            "player_id": "north-6",
            "question": "How involved has he been?",
        },
    ).json()
    assert answer["generation_mode"] == "model"
    assert answer["status"] == "reviewed"
    assert len(answer["trace"]) == 5


def test_health_reports_configuration_without_claiming_connection(monkeypatch):
    monkeypatch.setenv("MATCHLENS_AI_MODE", "foundry")
    monkeypatch.delenv("AZURE_AI_PROJECT_ENDPOINT", raising=False)
    status = client.get("/api/health").json()
    assert status["ai_mode"] == "foundry"
    assert status["integration_status"] == "missing_configuration"
    assert status["cloud_connected"] is False


def test_shooting_and_causal_questions_are_relevant():
    match = client.get("/api/matches").json()[0]["id"]
    body = {"period": 2, "elapsed_ms": 1200000, "player_id": "north-6"}
    for language, question, expected in [
        ("en", "How many shots has he taken?", "shots"),
        ("es", "¿Cuántos tiros lleva?", "tiros"),
        ("en", "Did his passing cause the goal?", "causation"),
        ("es", "¿Sus pases causaron el gol?", "causalidad"),
    ]:
        result = client.post(
            f"/api/matches/{match}/questions",
            json={**body, "language": language, "question": question},
        ).json()
        assert expected in result["text"]


def test_single_policy_keeps_count_questions_deterministic(monkeypatch):
    import matchlens.api as api_module

    monkeypatch.setenv("MATCHLENS_AI_POLICY", "single")

    def unavailable():
        raise AssertionError("Count questions must not invoke a model")

    monkeypatch.setattr(api_module, "configured_provider", unavailable)
    match = client.get("/api/matches").json()[0]["id"]
    answer = client.post(
        f"/api/matches/{match}/questions",
        json={
            "period": 2,
            "elapsed_ms": 1200000,
            "player_id": "north-6",
            "question": "How many shots has he taken?",
        },
    ).json()
    assert answer["generation_mode"] == "template"
    assert "shots" in answer["text"]
