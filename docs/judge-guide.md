# MatchLens judge guide

Status: October 21, 2026. This is a local prototype using fictional clubs, players, matches and season baselines. Start with the [public template demo](https://matchlens-chris-demo-2026.azurewebsites.net) or the reproducible local build. No Azure account is required for either.

## Run the local build

Prerequisites: Python 3.12+, uv, Node.js 20+, npm. From the extracted repository root in PowerShell:

```powershell
uv sync --project backend --locked
Push-Location frontend
npm ci
npm run build
Pop-Location
./scripts/Start-MatchLens.ps1
```

Open http://127.0.0.1:8000. Keep the server bound to loopback. The launcher selects deterministic template mode without needing an account. Initial dependency installation requires network access; installed local template operation needs no model service. On macOS/Linux, build as above, set `MATCHLENS_AI_MODE=template` and `MATCHLENS_FRONTEND_DIR` to the absolute `frontend/dist` path, then run `backend/.venv/bin/python -m uvicorn matchlens.api:app --host 127.0.0.1 --port 8000`. The PowerShell launcher is Windows-specific.

## What to inspect

1. Select the shift scenario, initially at minute 70 with a minute-60 anchor. Compare recorded entries and routes, retaining the window/sample caveats.
2. Select a player, inspect match counts and the separately labeled synthetic season cohort. Open a key moment to inspect its supporting sequence.
3. Ask a passing or involvement question. Inspect the response mode and supporting event IDs. Seek backward and request a recap at the selected clock.
4. Switch Watch/Explore. The illustrated scene is generated from synthetic events; it is not encoded match video, tracking or video recognition.

The short recording plan is in [demo-script.md](demo-script.md). Technical boundaries are in [architecture.md](architecture.md) and [metrics.md](metrics.md).

## What the evidence supports

- Deterministic synthetic replay and event-backed analysis, with rule-based sanity checks over seeds 0–19: [data-validation.json](data-validation.json). These checks do not establish empirical calibration.
- Canonical SQLite event revisions served through the API. Administrator ingestion requires a server-side `MATCHLENS_INGEST_TOKEN` and matching `X-MatchLens-Token`; higher revisions replace earlier versions and stale/duplicate writes are ignored. This is a local ingestion demonstration, not a connected external live feed. Persistence requires `MATCHLENS_EVENT_DB`; the default is in memory.
- Same-origin serving of built frontend assets and a useful template fallback. See dated local checks in [build-ledger.md](build-ledger.md), rather than treating configuration as verification.
- Actual authenticated Foundry `gpt-4.1-mini` responses and usage were recorded: [foundry-verification.json](foundry-verification.json), [foundry-fresh-verification.json](foundry-fresh-verification.json). The fresh four-call check accepted output structure but failed semantic acceptance. It is not evidence of trustworthy interpretations or broad reliability.
- Historical policy measurements and quality failures are recorded in [evaluation.md](evaluation.md) and [evaluation-results.json](evaluation-results.json). The raw-policy timing/token comparison does not measure the later hybrid routing policy. A conditional Global Standard retail estimate is recorded in evaluation-results.json and price-reference.json; the deployment SKU and actual Azure bill remain unverified. Independent bilingual acceptance remains unverified.

The optional `single` model policy keeps direct-count answers deterministic and may call a model for interpretation. `specialist` is experimental canonical sentence selection, not a validated advantage. Read template/model/fallback disclosures on each output. Structural citation and number validation does not prove semantic support. Use template mode for the core demonstration.

## Reproduce checks and package

```powershell
New-Item -ItemType Directory -Force artifacts | Out-Null
backend/.venv/Scripts/python.exe -m pytest backend/tests --basetemp artifacts/pytest -q
backend/.venv/Scripts/ruff.exe check backend
Push-Location frontend
npm test -- --reporter=dot
npm run build
Pop-Location
backend/.venv/Scripts/python.exe scripts/package_judge.py --output artifacts/matchlens-judge.zip
```

The ZIP contains current working-tree bytes for eligible Git-tracked files, these handoff documents/script, a generated placeholder-only `.env.example`, `START-HERE.md`, and a SHA-256 manifest. It excludes environment secrets, dependencies, caches, Git internals and default local artifacts. `--evidence path/to/file` explicitly adds a reviewed evidence file. The packager performs exclusion/credential checks and verifies archive integrity and hashes; this does not certify all prose free of sensitive information. Review optional evidence before supplying it. No `.env` is loaded by packaging.

## Remaining limitations and submission work

Public source: https://github.com/chrisantosiewicz/MatchLens. The public template application is verified (hosting-verification.json); final competition submission is not claimed. The local build remains available. Licensing/asset provenance and final competition access requirements need owner review before submission. Source-revision invalidation, actual window durations and concurrent SQLite reads have regression coverage. Model requests have a process-local demo budget; there is no public authentication or distributed quota. Authenticated current-contract and fresh-seed evaluation completed; overall semantic acceptance remains false (foundry-current-verification.json). Never infer causation or off-ball behavior from event sequences.
