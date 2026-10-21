"""Same-origin serving for a built local demo; not public model access control."""

from pathlib import Path

from fastapi.staticfiles import StaticFiles


def mount_frontend(app, directory):
    directory = Path(directory).resolve()
    if not (directory / "index.html").is_file():
        raise RuntimeError("Build the frontend before setting MATCHLENS_FRONTEND_DIR")
    app.mount("/", StaticFiles(directory=directory, html=True), name="frontend")
