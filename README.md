# MatchLens

**Every moment matters. See what changed. Understand who made it happen.**

**[Open the public demo](https://matchlens-chris-demo-2026.azurewebsites.net)** — Azure free-tier hosting, deterministic template mode.

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

On macOS/Linux, use `backend/.venv/bin/python` instead of the Windows interpreter path. Keep these development servers bound to loopback: this local prototype has no production authentication. Model work has a process-local request budget, which is not distributed access control.

## Try it

1. Select a match scenario. The replay opens at minute 70 with a minute-60 comparison anchor.
2. Inspect box entries, routes and recorded action counts. The small-sample caveat is deliberate.
3. Select a player on the action map or in the squad. Season bars compare eligible fictional peers; today's values are separate match counts.
4. Open **Key moments**, then a moment to highlight its recorded sequence.
5. Ask about passing, involvement, changes since the anchor, or the synthetic season baseline.
6. Switch explanation depth and English/Spanish, seek back, or build a clock-limited recap.
7. Use the expand icon for a presentation preview. This is not yet a published/synchronized OBS output.

Use **Watch / Explore** to inspect the companion layout: Watch puts an illustrative synthetic scene above a compact two-team action map; Explore retains the analysis workspace and a small scene preview. This is **not actual encoded video or computer-vision recognition**. Milestone cards are computed from synthetic events, and numbered markers use roster IDs. See `docs/watch-companion.md` for boundaries and remaining video work.

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

## Inspect recorded AI evidence

[Open all frozen cases and source-event proof](https://matchlens-chris-demo-2026.azurewebsites.net/evidence/index.html). This is recorded model output, not live generation. Complete metric sources and actual model citations are shown separately. Independent human review is pending. Paused visible views check event corrections every15seconds without moving the clock.

## Football meaning

Answers can now show a concrete build-up or turnover sequence, why that recorded contribution matters, and its limits. Expand **The moment behind the explanation** to inspect it. [Situations where your football judgment helps](docs/football-meaning-review.md). Model generation remains experimental; all current trial outcomes are visible in recorded evidence.

## Location-aware editorial context

Hover an action for its event location, then ask about the player. Answers lead with the recorded sequence, measured pass origin/destination, and build-up role. Expand **Location, role & editorial context** for exposure, same-metric comparison gates and coverage limits. These are provisional editorial policies; geometry does not establish intent or defensive-line breaks. Recorded AI candidates and their review failures remain separate from the current guarded fallback.

## Current stage

See [STATUS.md](STATUS.md) for the authoritative dated implementation and submission status. Older experiment reports are historical evidence.


Implemented: synthetic replay; deterministic clock-limited metrics, profiles, fictional positional percentiles, key moments, questions and recaps; English/Spanish presentation; Watch/Explore; progressive-pass alerts; canonical SQLite revisions and token-protected local ingestion. The Watch scene is an SVG illustration, not video recognition or tracking.

**Foundry connectivity is verified; semantic quality is experimental.** Authenticated `gpt-4.1-mini` calls returned outputs and usage. Initial held-out evaluation exposed incorrect subject/time-window interpretations, including unequal-window comparisons. The current implementation supplies calculated per-minute rates, active player minutes, evidence IDs and uncertainty, and rejects a mismatched rate-comparison contract. A current-policy paired live run completed: rate comparisons improved, but subject wording and unsupported area-presence descriptions still failed developer semantic review. See [current results](docs/evaluation-current-results.json). Follow-up changes have fresh developer-reviewed traces, but overall semantic acceptance remains false. Default local operation uses deterministic templates and remains useful without Azure.

The single-model policy keeps direct-count questions and all Spanish requests deterministic; optional English why/change interpretation remains experimental. The specialist workflow is retained for evaluation, with no demonstrated quality advantage. Historical measurements and limitations are in [evaluation](docs/evaluation.md). No broad analytical accuracy, independent bilingual acceptance, or production reliability is claimed.

No real footage, off-ball tracking, real league rankings, licensed match data or predictive models are included. Synthetic realism is rule-based, not empirically calibrated. Public source: [MatchLens on GitHub](https://github.com/chrisantosiewicz/MatchLens). A 105-second captioned walkthrough accompanies the release; it uses edited screenshots of actual template-mode operation. Start with the [judge guide](docs/judge-guide.md) and [architecture](docs/architecture.md).

## Recovery milestones and built-demo serving

See [submission checklist](docs/submission-checklist.md) for review triage, dependencies and acceptance criteria. [AGENTS.md](AGENTS.md) defines project rules. Data checks across seeds 0–19 are recorded in [data validation](docs/data-validation.json); these are heuristic sanity checks, not empirical calibration. Sparse data is a missing-observation sample of the corresponding complete `null` fixture (same seed). Its final score is simulator ground truth; the API computes the observed score from visible events, which can be incomplete.

To serve the built demo without the Vite proxy, first run `npm ci` and `npm run build` in `frontend`, then from the repository root:

```powershell
$env:MATCHLENS_FRONTEND_DIR = (Resolve-Path frontend/dist).Path
backend/.venv/Scripts/python.exe -m uvicorn matchlens.api:app --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000. This is reproducible built-demo serving, not a claim of production hardening. Do not expose a paid model endpoint publicly before access limits are implemented.

### Optional Foundry candidate and evaluation

```powershell
uv sync --project backend --extra foundry --locked
$env:MATCHLENS_AI_MODE = 'foundry'
$env:MATCHLENS_AI_POLICY = 'single'
# Set AZURE_AI_PROJECT_ENDPOINT and AZURE_AI_MODEL_DEPLOYMENT_NAME locally.
# Authenticate locally with an Entra credential supported by DefaultAzureCredential.
```

No environment file is loaded automatically. Restart the server after configuration changes. `single` opts into an experimental free-form interpretation using a calculated context packet; `specialist` retains canonical sentence selection for optional comparison; the default single policy keeps direct counts deterministic. Live connectivity is verified, but neither has met semantic-quality acceptance criteria. Unsupported tracking and causal questions are conservatively answered before model invocation. Unknown citations/numeric tokens trigger fallback; matching tokens do not establish semantic support. Human evaluation is required before claiming trustworthy explanations.

Offline paired evaluation:

```powershell
backend/.venv/Scripts/python.exe -m matchlens.evaluate --output artifacts/evaluation.json
```

Add `--live` only with configured, authenticated Foundry access: it makes billable requests. See [evaluation protocol](docs/evaluation.md). Initial live latency/token measurements and observed quality failures are recorded in docs/evaluation-results.json; current-policy acceptance remains unverified. A conditional Global Standard retail estimate for the initial experiment is recorded alongside token usage; it is not an Azure bill.


### Current local launcher and corrections

After building the frontend, run `./scripts/Start-MatchLens.ps1` for account-free template mode, or `./scripts/Start-MatchLens.ps1 -Foundry` to explicitly opt into the locally configured project. The launcher reads only whitelisted configuration from ignored `.env`; it binds to loopback and never prints secrets. Browser authentication is opt-in (`MATCHLENS_ALLOW_BROWSER_LOGIN=1`) with explicit `AZURE_TENANT_ID`. Tokens are kept in process memory; another process may require sign-in again.

`POST /api/matches/{id}/events` accepts synthetic events/revisions only when the server has `MATCHLENS_INGEST_TOKEN` and the caller supplies the matching `X-MatchLens-Token` header. No token belongs in browser code. Higher revisions replace earlier events; duplicates/stale revisions are ignored. State/statistics/alerts/answers/recaps read canonical events afterward. Set `MATCHLENS_EVENT_DB` to a local SQLite path for restart persistence. This is a local ingestion demonstration, not an authenticated external feed connector. Responses carry a canonical source revision. On the next fetch, the viewer invalidates old narratives and rejects mixed-revision snapshots; paused views receive no background correction notification. Model work defaults to six requests per minute and fifty requests per process session. This is a demo work budget, not a dollar cap or public access-control system.

Free-only hosting preparation and exact deployment boundaries: [deployment guide](docs/deployment.md). Anonymous public application checks pass; see [hosting verification](docs/hosting-verification.json). Free-tier cold starts and quotas apply.

A fresh six-case check of the revised prompt produced five structurally accepted explanations and one abstention. Developer review found four supported explanations and one Spanish failure; overall quality remains unaccepted. See [current Foundry verification](docs/foundry-current-verification.json). Public hosting uses templates; no paid model endpoint is exposed.

Three-role recommendation workflow and sentence-level evidence: [implementation, setup and limits](docs/evidence-chain.md). Opt-in policy `evidence_chain`; public paid model calls remain disabled.

Latest judge response: [fair same-ledger evaluation and limitations](docs/fair-canonical-evaluation.md). [Football decisions and actual recorded Foundry execution](https://matchlens-chris-demo-2026.azurewebsites.net/review/). [Phone-friendly human review protocol](docs/human-review-protocol.md); real participant results remain pending.
