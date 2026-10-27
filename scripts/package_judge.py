"""Build and verify a local judge handoff without reading environment secrets."""

import argparse
import hashlib
import json
import re
import subprocess
import zipfile
from pathlib import Path, PurePosixPath

HANDOFF = (
    "docs/judge-guide.md",
    "docs/demo-script.md",
    "docs/architecture.md",
    "scripts/package_judge.py",
    "scripts/test_package_judge.py",
)
EXCLUDED_PARTS = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    ".mypy_cache",
    ".aws",
    ".azure",
    ".codex",
    ".agents",
    "artifacts",
    "dist",
    "coverage",
    "htmlcov",
}
SECRET_SUFFIXES = {".pem", ".key", ".pfx", ".p12", ".sqlite", ".db", ".zip", ".pyc"}
SECRET_TEXT = re.compile(
    rb"-----BEGIN (?:[A-Z ]+ )?PRIVATE KEY-----|"
    rb"(?:AccountKey|SharedAccessSignature|client_secret|api_key|api-key|access_token)"
    rb"\s*[=:]\s*[\"']?[A-Za-z0-9_+/.-]{20,}|"
    rb"(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|sk-[A-Za-z0-9]{30,})",
    re.IGNORECASE,
)
EXAMPLE = """# Placeholder-only configuration; default demo requires no credentials.
MATCHLENS_AI_MODE=template
# MATCHLENS_AI_POLICY=single
# AZURE_TENANT_ID=YOUR-TENANT-ID
# AZURE_AI_PROJECT_ENDPOINT=https://YOUR-RESOURCE.services.ai.azure.com/api/projects/YOUR-PROJECT
# AZURE_AI_MODEL_DEPLOYMENT_NAME=YOUR-DEPLOYMENT
# MATCHLENS_ALLOW_BROWSER_LOGIN=1
# MATCHLENS_INGEST_TOKEN=SET-LOCALLY-NEVER-IN-BROWSER
# MATCHLENS_EVENT_DB=artifacts/events.sqlite
# MATCHLENS_FRONTEND_DIR=C:/YOUR-CHECKOUT/frontend/dist
# MATCHLENS_AI_MODE=foundry
# Do not put real credentials in source or browser code. Nothing loads this file automatically.
"""
START = """# Start here: MatchLens local judge handoff

Read docs/judge-guide.md for setup, evidence and known limitations.
docs/demo-script.md describes the current narrated edited UI demonstration and its disclosures.
docs/architecture.md explains the deterministic and optional model paths.

All football data is fictional and synthetic. The Watch scene is illustrative,
not encoded footage or computer vision. Default operation is template mode.
Live Foundry connectivity is recorded; semantic reliability is not established.

MANIFEST.json records SHA-256 hashes for every other archive entry, the Git HEAD,
and tracked-file modifications at packaging time. Current working-tree content
is included, so this archive need not equal the HEAD commit. Dependencies,
build output, environment secrets and local caches are excluded. Install/build
using the guide. Optional evidence appears under evidence/.

This is a local source handoff, not proof of public hosting, license clearance,
competition submission, or an accepted model-quality evaluation.
"""


def eligible(name):
    """Reject secret-bearing names and generated directories before reading bytes."""
    path = PurePosixPath(name)
    parts = [part.lower() for part in path.parts]
    if path.is_absolute() or ".." in parts or not parts:
        return False
    if any(part in EXCLUDED_PARTS for part in parts):
        return False
    base = parts[-1]
    if base == ".env.example":
        return True
    if base.startswith(".env") or base.endswith(".env"):
        return False
    if any(
        word in base
        for word in ("credential", "secret", "token-cache", "id_rsa", "id_ed25519")
    ):
        return False
    return path.suffix.lower() not in SECRET_SUFFIXES


def read_safe(path, root):
    if path.is_symlink():
        raise ValueError(f"Symlinks are not packaged: {path.name}")
    resolved = path.resolve(strict=True)
    if root is not None and not resolved.is_relative_to(root):
        raise ValueError("Package input escapes repository")
    content = resolved.read_bytes()
    if SECRET_TEXT.search(content):
        raise ValueError(
            f"Possible credential detected; excluded without printing content: {path.name}"
        )
    return content


def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args])


def verify(archive):
    with zipfile.ZipFile(archive) as bundle:
        if bundle.testzip() is not None:
            raise ValueError("ZIP CRC verification failed")
        names = bundle.namelist()
        if len(names) != len(set(names)):
            raise ValueError("Duplicate ZIP member")
        manifest = json.loads(bundle.read("MANIFEST.json"))
        expected = manifest["files"]
        if set(names) != set(expected) | {"MANIFEST.json"}:
            raise ValueError("ZIP member set differs from manifest")
        for name, details in expected.items():
            data = bundle.read(name)
            if (
                len(data) != details["bytes"]
                or hashlib.sha256(data).hexdigest() != details["sha256"]
            ):
                raise ValueError(f"Hash verification failed: {name}")
    return len(expected)


def package(root, output, evidence):
    root = root.resolve()
    output = output.resolve()
    if output.exists():
        raise ValueError("Output exists; choose a new output path")
    tracked = git(root, "ls-files", "-z").decode("utf-8").split("\0")
    entries = {}
    excluded = []
    for name in sorted(set(filter(None, tracked)) | set(HANDOFF)):
        if name == ".env.example":
            continue  # Never read configuration; generate placeholders below.
        if not eligible(name):
            excluded.append(name)
            continue
        path = root / name
        if not path.is_file():
            excluded.append(name)
            continue
        if path.resolve() == output:
            continue
        entries[name] = read_safe(path, root)
    for index, path in enumerate(evidence, 1):
        if not eligible(path.name) or path.name == ".env.example":
            raise ValueError(f"Ineligible evidence filename: {path.name}")
        entries[f"evidence/{index:02d}-{path.name}"] = read_safe(path, None)
    entries[".env.example"] = EXAMPLE.encode("utf-8")
    entries["START-HERE.md"] = START.encode("utf-8")
    manifest = {
        "format": 1,
        "git_head": git(root, "rev-parse", "HEAD").decode().strip(),
        "tracked_changes": git(root, "diff", "HEAD", "--name-only")
        .decode()
        .splitlines(),
        "content_basis": "Current working-tree bytes; no execution or quality certification",
        "excluded_tracked_paths": excluded,
        "files": {
            name: {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
            for name, data in sorted(entries.items())
        },
    }
    entries["MANIFEST.json"] = (json.dumps(manifest, indent=2) + "\n").encode()
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "x", compression=zipfile.ZIP_DEFLATED) as bundle:
        for name, data in sorted(entries.items()):
            bundle.writestr(name, data)
    return verify(output)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, default=Path("artifacts/matchlens-judge.zip")
    )
    parser.add_argument("--evidence", type=Path, action="append", default=[])
    parser.add_argument(
        "--verify", type=Path, help="Verify an existing package instead of creating one"
    )
    args = parser.parse_args()
    try:
        if args.verify:
            count = verify(args.verify)
            print(f"Verified {count} payload files: {args.verify}")
        else:
            count = package(
                Path(__file__).resolve().parents[1], args.output, args.evidence
            )
            print(f"Created and verified {count} payload files: {args.output}")
    except (
        OSError,
        ValueError,
        subprocess.CalledProcessError,
        zipfile.BadZipFile,
    ) as error:
        parser.exit(1, f"Packaging failed: {error}\n")


if __name__ == "__main__":
    main()
