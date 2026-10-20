# MatchLens

**Every moment matters. See what changed. Understand who made it happen.**

An event-backed football analysis workspace for the Inside the Game hackathon. All clubs, players, matches and season profiles are fictional.

## Run locally (Windows PowerShell)

Prerequisites: Python 3.12+, uv, Node.js 20+ and npm.

Terminal 1, repository root:

```powershell
uv sync --project backend
backend/.venv/Scripts/python.exe -m uvicorn matchlens.api:app --host 127.0.0.1 --port 8000
```

Terminal 2:

```powershell
cd frontend
npm ci
npm run dev -- --port 5173
```

Open http://127.0.0.1:5173. API documentation: http://127.0.0.1:8000/docs.

On macOS/Linux, use `backend/.venv/bin/python` instead of the Windows interpreter path. Keep these development servers bound to loopback: this local prototype has no production authentication or rate limiting.

## Try it

1. Select a match scenario. The replay opens at minute 70 with a minute-60 comparison anchor.
2. Inspect box entries, routes and recorded action counts. The small-sample caveat is deliberate.
3. Select a player on the action map or in the squad. Season bars compare eligible fictional peers; today's values are separate match counts.
4. Open **Key moments**, then a moment to highlight its recorded sequence.
5. Ask about passing, involvement, changes since the anchor, or the synthetic season baseline.
6. Switch explanation depth and English/Spanish, seek back, or build a clock-limited recap.
7. Use the expand icon for a presentation preview. This is not yet a published/synchronized OBS output.

## Verification

```powershell
New-Item -ItemType Directory -Force artifacts | Out-Null
backend/.venv/Scripts/python.exe -m pytest backend/tests --basetemp artifacts/pytest -q
cd frontend
npm test
npm run build
```

Tests include independently expected analytics counts, cohort/tie handling, revision storage, moment attribution, and delayed-response spoiler prevention. Some Windows sandboxes prevent local TestClient threads from completing; run in a normal terminal when needed.

Generate versioned example data from repository root:

```powershell
backend/.venv/Scripts/python.exe -m matchlens.synthetic --output data
```

## Current stage

Implemented: local synthetic replay, before/after metrics, player profiles and percentile bars, key event sequences, bounded template questions, English/Spanish analytical text, and template recaps. SQLite revision storage is tested separately; the demo API currently serves deterministic in-memory fixtures. Polling updates the viewer's requested clock; live SSE ingestion is not implemented yet.

**AI is not connected.** Question/recap responses are explicitly labeled deterministic templates. The bounded Analyst → Reviewer → Producer orchestration is implemented and tested with a scripted provider. It chooses allowed tools, supports one revision, rejects unknown fact IDs/changed sentences, and falls back on failure. The optional Foundry adapter is written but has not been installed or tested against an actual project. See `.env.example`; nothing is loaded from that file automatically, and no live requests occur in default template mode.

Azure subscription/Foundry setup is not available yet. Live-agent evaluation, cloud deployment, durable publication/authentication, actual overlay scheduling/retractions, and full localization remain subsequent milestones. Never describe this local build as a finished AI submission. The current producer selects and orders canonical factual sentences; unrestricted generated explanations are intentionally withheld pending evaluation.

No real footage, live tracking, off-ball movement, real league rankings, licensed data or predictive models are included. External font delivery is optional; system-font fallbacks remain usable offline. Synthetic realism is rule-based, not empirically calibrated. Season profiles are illustrative fictional baselines and not real European competition rankings.

Design and implementation plan: `docs/superpowers/`. Build decisions and actual validation: `docs/build-ledger.md`.
