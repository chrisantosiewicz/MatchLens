# MatchLens Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking. Native execution is recommended; user selection is pending.

**Goal:** Deliver the approved synthetic football analysis prototype from replay to personalized graphics and recaps.

**Architecture:** Revision-aware event storage feeds deterministic analytics and a bounded three-role AI workflow. A React application presents the shared evidence through host, fan, and presentation routes. Local operation precedes Azure adapters, with no mock cloud claims.

**Tech Stack:** Python 3.12+, FastAPI, Pydantic, pytest, React, TypeScript, Vite, Vitest, PostgreSQL, Azure Service Bus/Blob/Container Apps, Microsoft Foundry.

**Spec:** ../specs/2026-10-20-matchlens-design.md

## Global Constraints

- All football records are synthetic.
- Default comparison: ten minutes of match-clock time before and after selected anchor, within the same period.
- Suppress directional pattern language with fewer than five entries in either comparison window.
- Cohort: same broad position, at least 900 season minutes, across five fictional competitions. Hide percentile if fewer than 30 eligible peers.
- Midrank percentile: 100*(strictly lower + 0.5*equal)/N.
- At most two analytical attempts and eight tool calls per request.
- Public submission video strictly less than two minutes; target 110 seconds.
- No future information beyond the viewer clock. No inferred continuous player locations or causal substitution claims.

## Review Focus

- Boundary timestamps and halftime direction: use period-aware windows and explicit inclusive/exclusive boundaries (Task 2).
- Corrections arriving after publication: recompute and retract dependent findings (Tasks 2 and 6).
- Players with no actions or substituted off: selectable lineup and correct minutes/empty state (Tasks 3 and 4).
- Model outputs containing invented evidence or numeric values: reject and produce factual fallback (Task 5).
- Deployment without model credentials or unavailable infrastructure: truthful disabled/fallback states and actionable health checks (Tasks 5 and 8).

## File structure

`backend/matchlens/`: models.py (contracts), synthetic.py (fixtures), store.py (revision state), analytics.py (metrics), profiles.py (cohorts), moments.py (sequences), workflow.py (bounded orchestration), providers.py (model adapter), stories.py (publication/recaps), api.py (HTTP/SSE), cloud.py (Azure adapters).

`backend/tests/`: independently expected fixture tests, contract tests, workflow/recovery tests.

`frontend/src/`: contracts.ts, api.ts, App.tsx, styles.css; components/Pitch.tsx, Timeline.tsx, PlayerPanel.tsx, EvidencePanel.tsx, StoryCard.tsx; views/Host.tsx, Fan.tsx, Presentation.tsx.

`data/`: generated versioned fixtures and scenario manifest without secrets. `evals/`: question set, baseline runner, results. `infra/`: deploy configuration, environment template. `docs/`: setup, metrics, data generation, evaluation, demo, and known limits.

Each task follows RED → minimal implementation → GREEN. Commit only task-related files if a Git repository exists; otherwise initialize a local repository before implementation after checking parent repository ownership. No remote push or deployment credentials are assumed.

### Task 1: Reproducible synthetic match and season contracts

**Files:** backend/pyproject.toml; backend/matchlens/{__init__,models,synthetic}.py; backend/tests/test_synthetic.py; .gitignore.

**Interfaces:** `generate_match(seed: int, scenario: str) -> MatchFixture`; `generate_seasons(seed: int) -> list[SeasonRecord]`. MatchFixture includes schema version, metadata, lineup and events; Pydantic types implement spec event fields. Use six broad position groups, at least 40 qualifying players per group, distributed across five fictional competitions, with demo players included. Season records contain minutes and raw counts for four metrics.

- [ ] Write `test_seed_reproducible`, `test_valid_score_and_active_players`, `test_five_leagues_and_eligible_cohorts`: assert identical seeds produce identical serialized fixtures, invalid actors never occur, goal totals equal final score, every eligible position has >=30 peers, and no season includes current match.
- [ ] Run `uv run --project backend pytest backend/tests/test_synthetic.py -q`; confirm failure before implementation.
- [ ] Implement models and seeded possession generator, plus CLI `python -m matchlens.synthetic --output data` for shift/null/sparse fixtures. Scenario labels remain in manifest outside event payloads.
- [ ] Repeat tests; generate fixtures and validate them. Record assumptions rather than claiming calibrated realism.
- [ ] Commit tested contracts/generator and generated example fixtures.

### Task 2: Event store and match analytics

**Files:** backend/matchlens/{store,analytics}.py; backend/tests/{test_store,test_analytics}.py.

**Interfaces:** `EventStore.upsert(event: Event) -> ChangeSet`; `events_at(period: int, elapsed_ms: int) -> list[Event]`; `compare_windows(events, anchor, viewer_clock) -> Comparison`; `player_stats(events, player_id, viewer_clock) -> PlayerStats`. ChangeSet names invalidated event IDs and revision. MVP SQLite implementation persists canonical events and checkpoints.

- [ ] Write independent hand-authored fixtures: 2 versus 6 box entries; right-route counts; exact 10m progression boundary; halftime reversal; zero attempts. Assert sparse samples have `pattern_supported == False`; after-window is provisional until complete; no future event included. Window convention: before [anchor-600000, anchor), after [anchor, min(anchor+600000, viewer clock)].
- [ ] Write duplicate/revision/restart tests: duplicate changes no totals; higher revision replaces action; stale revision ignored; reopened store returns same state.
- [ ] Run corresponding pytest files and observe failures.
- [ ] Implement metric definitions from spec, revision storage, and period-aware reconstruction.
- [ ] Run tests; commit implementation and expected-value fixtures.

### Task 3: Player profiles and recorded moments

**Files:** backend/matchlens/{profiles,moments}.py; backend/tests/{test_profiles,test_moments}.py.

**Interfaces:** `profile(player_id, seasons) -> PlayerProfile`; `key_moments(events, player_id, viewer_clock, limit=5) -> list[PlayerMoment]`. Each moment has reason, source IDs, period/time, and bounded sequence. Profile includes cohort eligibility, N, values and percentiles.

- [ ] Write percentile test: peer values [1,2,2,4] give selected value 2 a midrank of 50%; fewer than 30 peers hides display; 899 minutes excluded. Use larger tied fixture for rendered eligibility.
- [ ] Write moment tests for shot-ending possession, turnover then opposition shot, future-event exclusion, no-action player, and hard five-item limit; assert no off-ball or causal claim.
- [ ] Run tests to see failures; implement functions and stable deterministic ordering.
- [ ] Run tests; commit profiles and moments.

### Task 4: Usable local replay and interactive player screen

**Files:** backend/matchlens/api.py; backend/tests/test_api.py; frontend/package.json, tsconfig.json, vite.config.ts, index.html; frontend/src contracts/API/components/views/styles listed above; frontend tests.

**Interfaces:** GET /api/matches, GET /api/matches/{id}/state?period=&elapsed_ms=, GET /api/matches/{id}/players/{player_id}?period=&elapsed_ms=, GET /api/matches/{id}/comparison?period=&anchor_ms=&elapsed_ms=. Responses serialize earlier task types. Replay clock is explicit per client, never a global mutable clock.

- [ ] Write API tests asserting selected-player moments/profile/statistics obey requested clock; unknown IDs return 404 and invalid clocks 422.
- [ ] Write UI behavior tests for lineup selection with no events, keyboard-selectable markers, period change, opening a moment and changing the evidence sequence, and separate viewer clocks.
- [ ] Observe failing tests, then implement local API and polished responsive dashboard: dark broadcast canvas, legible score rail, spacious pitch maps, drawer and timeline; distinguish synthetic history and today's numbers.
- [ ] Run backend tests, frontend tests, TypeScript/build. Open local app and visually inspect desktop/mobile; correct layout issues before completing.
- [ ] Commit working local vertical slice with startup instructions.

### Task 5: Tool-using AI workflow, questions and multilingual findings

**Files:** backend/matchlens/{workflow,providers}.py; backend/tests/test_workflow.py; evals/questions.jsonl; docs/ai-workflow.md.

**Interfaces:** `answer(request: AnalysisRequest, tools: AnalyticsTools, provider: ModelProvider) -> ReviewedStory`; `ModelProvider.complete(role, state, tool_results) -> structured response`. Tools only call earlier analytics/profile/moment interfaces. AnalysisRequest carries viewer clock/preferences; ReviewedStory carries evidence, review, generation mode and localized variants. Implement Foundry adapter after confirming current official SDK/docs; secrets server-side.

- [ ] Write scripted-provider tests for Analyst→Reviewer→Producer state transitions, revision once, abstention, eight-call cap, fake evidence, invented numbers, unsupported tracking questions, timeout fallback, and no credentials. Assert failures cannot publish generated unverified prose.
- [ ] Run failing tests; implement typed orchestration, deterministic claim validation and factual templates. Missing credentials show explicit template mode, not simulated live AI.
- [ ] Add bounded question intent mapping, English/Spanish output, evidence-aware answer panel. Validate selected-player constraints and viewer clock on every tool call.
- [ ] Run workflow/API/UI tests and real endpoint smoke test when credentials exist; otherwise document cloud AI unverified.
- [ ] Commit workflow and question fixtures.

### Task 6: Publication, synchronization and recaps

**Files:** backend/matchlens/stories.py; backend/tests/test_stories.py; API additions; frontend views and StoryCard; frontend synchronization tests.

**Interfaces:** `approve(story_id, actor) -> OverlaySpec`; `invalidate(event_ids) -> list[Retraction]`; `recap(match_id, viewer_clock, preferences) -> Recap`. Durable story ledger stores revision, evidence, approval and generation mode. Host mutation routes require server-validated credentials; read-only routes cannot approve. Local development has explicitly documented auth configuration.

- [ ] Write tests for unauthorized publication, expiry, correction retraction, delayed generated story scheduling, independent viewer offsets, seek spoiler prevention, and recap authoritative score after revisions.
- [ ] Observe failure, implement story persistence/API and one transparent browser overlay template. Complete English/Spanish and casual/analyst rendering; preferences change selection and detail.
- [ ] Run integration tests and load overlay in a browser; optionally test OBS if available without claiming unperformed integration.
- [ ] Commit full local pipeline.

### Task 7: Evaluation and operational verification

**Files:** evals/run.py, evals/report.md; backend/tests/test_recovery.py; docs/{metrics,data-generation,accessibility,demo}.md.

**Interfaces:** evaluation runner consumes versioned questions and same tools under single-agent and three-role policies; outputs factual correctness, abstention, latency and provider usage without secrets.

- [ ] Write failing tests for evaluation result accounting and held-out seed isolation; implement runner, then run tests.
- [ ] Evaluate at least ten metric fixtures, review 50 outputs, and review 20 English/Spanish pairs when model/reviewer access permits. Record missing coverage explicitly.
- [ ] Run duplicate/restart/correction tests and measured load/latency checks. Perform keyboard/mobile checks; do not claim production-scale readiness.
- [ ] Attempt three host tasks if participants available; report actual sample and observations, no invented users or payment claims.
- [ ] Commit actual evaluation artifacts and 110-second demo script.

### Task 8: Azure adapters and submission-ready packaging

**Files:** backend/matchlens/cloud.py; backend/tests/test_cloud_contracts.py; infra deployment templates; Dockerfile; .env.example; README.md; docs/{deployment,testing,limitations}.md; CI workflow.

**Interfaces:** Azure event adapter implements EventStore/processing semantics from Task 2; Service Bus acknowledges only after durable commit; failed messages retry/dead-letter. PostgreSQL persists events/story ledger; Blob stores fixtures; Container Apps runs API/worker; telemetry links request/event/story IDs.

- [ ] Write failing adapter contract tests for durable acknowledgment, retry, health/missing configuration, and secret exclusion. Implement adapters and deployment configuration.
- [ ] Run backend/frontend/build checks, container startup and adapter tests. Verify deployed model/service compatibility using official current docs.
- [ ] Deploy only with available account authorization and required runtime approvals. Report actual services and limitations. Keep local app usable if account setup is blocked.
- [ ] Verify public repository URL, judge access, English instructions, licensing/assets, video public link <120 seconds, and judging availability end date. Remote publication and final submission require concrete account targets and access; do not invent them.
- [ ] Commit packaging. Perform whole-change review, address material findings, and record remaining limits before claiming completion.

## Handoff

Plan self-review: all approved features map to Tasks 1–8. Cross-task contracts consistently use period-aware viewer clocks and revision-aware provenance. Primary external dependencies are Azure subscription/Foundry access, actual bilingual/user evaluation, repository destination, and judge end date; none is silently assumed complete.

Recommended execution: native in this chat. The tightly shared event and evidence contracts favor one implementer; use a fresh final review where authorized/available. Written-plan review and execution-method selection precede implementation under the planning skill.
