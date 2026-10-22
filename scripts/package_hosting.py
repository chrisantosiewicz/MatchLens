"""Package only production Python sources and built frontend, without credentials."""

import argparse
import subprocess
import tempfile
import zipfile
from pathlib import Path

from package_judge import SECRET_TEXT


def package(root, output):
    root, output = Path(root).resolve(), Path(output).resolve()
    if output.exists():
        raise FileExistsError(output)
    frontend = root / "frontend/dist"
    if not (frontend / "index.html").is_file():
        raise RuntimeError("Build frontend first")
    with tempfile.TemporaryDirectory() as scratch:
        requirements = Path(scratch) / "requirements.txt"
        subprocess.run(
            [
                "uv",
                "export",
                "--project",
                str(root / "backend"),
                "--locked",
                "--no-dev",
                "--no-emit-project",
                "--no-hashes",
                "--output-file",
                str(requirements),
            ],
            check=True,
            capture_output=True,
        )
        payload = {"requirements.txt": requirements.read_bytes()}
        for path in (root / "backend/matchlens").rglob("*.py"):
            if path.is_symlink():
                raise ValueError("Symlinks are not deployable")
            payload[path.relative_to(root / "backend").as_posix()] = path.read_bytes()
        for path in frontend.rglob("*"):
            if path.is_file():
                if path.is_symlink():
                    raise ValueError("Symlinks are not deployable")
                payload["public/" + path.relative_to(frontend).as_posix()] = (
                    path.read_bytes()
                )
        if any(SECRET_TEXT.search(data) for data in payload.values()):
            raise ValueError("Credential-like content detected")
        output.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(output, "x", zipfile.ZIP_DEFLATED) as archive:
            for name, data in sorted(payload.items()):
                archive.writestr(name, data)
        with zipfile.ZipFile(output) as archive:
            assert archive.testzip() is None
    print(f"Verified {len(payload)} production files: {output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    package(Path(__file__).resolve().parents[1], args.output)
