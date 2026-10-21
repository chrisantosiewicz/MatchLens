from fastapi import FastAPI
from fastapi.testclient import TestClient
from matchlens.serving import mount_frontend


def test_built_frontend_and_api_share_one_server(tmp_path):
    (tmp_path / "index.html").write_text("<h1>MatchLens</h1>")
    (tmp_path / "assets").mkdir()
    (tmp_path / "assets" / "app.js").write_text("window.loaded=true")
    app = FastAPI()

    @app.get("/api/health")
    def health():
        return {"status": "ok"}

    mount_frontend(app, tmp_path)
    client = TestClient(app)
    assert "MatchLens" in client.get("/").text
    assert client.get("/assets/app.js").status_code == 200
    assert client.get("/api/health").json() == {"status": "ok"}
    assert client.get("/.env").status_code == 404
