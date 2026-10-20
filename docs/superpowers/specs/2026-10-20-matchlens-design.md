# MatchLens design specification

Date: October 20, 2026. Status: ready for user review; implementation not started.

## Purpose and success

**Every moment matters. See what changed. Understand who made it happen.**

Build an AI-powered web prototype for the Inside the Game hackathon in seven days. Initial user: a football watch-along host or small production team. A fan companion consumes the same evidence with personalized selection, depth, and language.0 Demonstrate the complete ingest, interpret, explain, render, personalize pipeline and automated recaps. No prize outcome is guaranteed.

Success means a host can select a moment, inspect supported before/after findings, explore a player's contribution, ask a bounded question, and publish a synchronized graphic. Fans can independently explore at their own match clock without spoilers.

## Scope and screens

One workspace: score/clock/replay controls, event timeline, before/after pitch maps, three metric cards, evidence panel, and player drawer. Separate routes provide a read-only fan view and transparent presentation output. Producer controls require authentication on the public deployment; fan routes cannot mutate publication state.

1. **Since This Moment:** choose a timestamp, substitution, or goal. Compare box entries, entry routes, and recorded player involvement.
2. **Clickable players:** select a lineup entry or recorded event marker. Display match statistics, synthetic season profile, four percentile bars, and up to five key recorded moments available at the viewer clock. Event markers are action locations, never asserted live player positions.
3. **Player questions:** support involvement, passing destinations/completion, before/after change, and comparison with season baseline or eligible teammates. Free text maps to these intents. Unsupported tracking, predictions, and causal questions receive limitations and useful alternatives.
4. **Key recorded moments:** prioritize direct goal involvement, shot-ending possession contributions, shots, recoveries, and turnovers followed by opposition shots. Show the selection reason. Opening a moment selects an event sequence and schematic pitch animation, not video. Bound sequences by possession and the viewer clock. Never characterize a turnover as causing a goal solely through temporal order.
5. **Publish:** host approves a reviewed story into one reusable overlay template with duration and expiry; subsequent invalidation retracts it.
6. **Personalize:** team/player preference changes story ranking; casual mode gives one short explanation and a definition; analyst mode adds counts, denominators, windows, and caveats. English and Spanish cover cards, player answers, and recaps.
7. **Recap:** halftime/full-time and viewer-selected interval summaries assembled from accepted findings plus authoritative score/event state, honoring viewer clock and preferences.

## Data and metric contracts

All football records are synthetic. Fictional clubs, competitions, player identities, and original visual assets. No real footage, logos, historical player statistics, or scraped records.

Versioned event schema: match_id, event_id, revision, sequence, period, elapsed_ms, team_id, player_id, optional recipient_id, event_type, outcome, start/end coordinates, possession_id, and metadata. Lineups, pitch dimensions, direction per period, substitutions, score transitions, and explicit stoppage boundaries accompany events. Clock ordering uses period and elapsed time, not wall-clock receipt time.

Seeded possession-based generator maintains eligible players, coherent action locations, possession continuity, score, and boundaries. Scenarios: measurable attacking-route change; no clear change; sparse/disrupted feed. Hidden scenario labels are excluded from analysis inputs. Hold out extra seeds. Deliberately inject duplicates, corrections, and late arrivals for recovery checks. Publish generator assumptions; simulated validity is not real-feed validation.

Season records cover five fictional competitions and matching demo players, with positions, minutes, and consistent metric totals; exclude the current match. Four percentile metrics: completed passes per 90, progressive completed passes per 90, shots per 90, and recorded recoveries per 90. Cohort: same broad position, at least 900 season minutes, across those competitions. Hide percentile if fewer than 30 eligible peers. Use midrank percentile, 100*(strictly lower + 0.5*equal)/N, including selected player in N; label definition and sample size. Rankings remain stable throughout match.

Normalized pitch is 105 by 68 metres. A box entry is a completed pass/carry from outside into the attacking penalty area (16.5m deep, 40.32m wide). Route is the final entry's lateral third. Progressive pass: completed pass starting outside the attacking box and reducing Euclidean distance to goal centre by at least 10 metres. Explain this prototype definition; do not imply equivalence to a commercial provider's metric.

Player involvement counts recorded actions, not touches unless explicitly recorded. Completion displays attempts and completions. Today's counts and rates are separate from season percentiles; no inferred match percentile. No inferred continuous possession percentage without an explicit possession-time definition.

Default comparison: ten minutes of match-clock time before and after selected anchor, within the same period. Available shorter windows remain provisional and show actual duration. Cross-period comparison is disabled in MVP. Display counts, denominators, and duration. Suppress directional pattern language with fewer than five entries in either comparison window; display descriptive counts and insufficient-evidence message instead. Do not claim statistical significance or causal impact.

## AI workflow

Use Microsoft Foundry-backed models and a supported workflow SDK selected after verifying access. Three roles:

- Analyst chooses bounded tools for match windows, player metrics, cohort profile, and event sequences. Returns typed findings and evidence references.
- Reviewer challenges interpretation, samples, data quality, causal phrasing, and unsupported scope; accepts, requests revision, or abstains.
- Producer adapts accepted findings to audience, language, graphic constraints, and recap.

Shared state: request_id, viewer clock, preferences, selected anchor/player, tool results, evidence IDs, review verdict, attempt count, and publication version. At most two analytical attempts and eight tool calls per request. Deterministic code checks numerical values, names/IDs, windows, and provenance; AI review does not replace those checks. Model failure yields a labeled factual template, not a purported AI result. Unsupported claims are withheld. Recaps must not introduce new unsupported facts.

Capture workflow traces and compare with a single-agent baseline using identical questions/tools. Measure unsupported claims, useful answers, latency, and usage. Multi-agent superiority is an evaluation question, not an assumed result.

## Architecture and operations

React/TypeScript frontend with SVG pitch; Python/FastAPI backend; Server-Sent Events for updates. One repository, modular generator, analytics, workflow, API, and UI. Local development works with SQLite and local fixture replay; Azure deployment uses PostgreSQL for durable state, Blob Storage for fixtures, Service Bus for ingestion, and Container Apps for application and worker. Foundry supplies model inference/workflow support. Application Insights receives operational telemetry; confirm trace integration during setup.

Canonical revision-aware event storage supports idempotent processing and rebuilding affected aggregates. Commit durable processing state before acknowledging queue messages. Reconnect reconstructs state. Late corrections invalidate dependent findings and published versions. Retries are bounded; failed messages become inspectable dead letters. Secrets remain server-side; use managed identity where supported and documented environment settings otherwise. Do not expose private prompts or credentials through public traces.

Overlay contract: story_id, revision, period, match_time_start/end, display_duration_ms, expiry, language, audience, evidence references, approval status. Viewer-clock alignment is manually configured in MVP. Newly generated late stories schedule a new valid presentation interval or are discarded; never pretend to have rendered at a past time. Browser presentation URL is suitable for OBS browser-source testing; no claim of broadcast-system integration.

## Verification and evaluation

- All metrics agree with independently prepared expected values in at least ten fixtures, including direction changes and boundaries.
- Every published factual claim has structured provenance; review 50 generated outputs for unsupported numbers/entities, interpretation, and causal overstatement.
- Evaluate single-agent versus three-role workflow on the same versioned question set; publish results regardless of outcome.
- Metric update p95 <1 second after ingestion and generated story p95 <8 seconds in documented deployment conditions; identify fallback usage.
- Available scheduled overlays render within one second of configured clock; no future facts after seek or delayed viewing.
- Twenty English/Spanish pairs preserve facts/caveats; obtain bilingual terminology review or report review unavailable.
- Duplicates, worker restart, reconnect, timeout, late correction, and retraction tests pass.
- Recaps generated within 20 seconds under documented conditions and use authoritative final state.
- Three host usability sessions compare publication time and factual accuracy with current workflow if participants can be recruited. Report missing research honestly.
- Keyboard-accessible player selection and timeline controls, visible focus, high contrast, and non-colour-only encodings. Mobile fan view and desktop host view.

## Delivery and submission

Seven-day target assumes two developers and service access. Day 1: generator/contracts/access. Day 2: replay/state/pitch/player selection. Day 3: comparisons/profiles/moments. Day 4: agents/tools/evaluation baseline. Day 5: approval/overlay/personalization/languages/recap. Day 6: user evaluation, resilience, accessibility and polish. Day 7: freeze, deploy, document, record and submit.

Primary proposed category: Best Use of Microsoft Foundry. Supporting category evidence: agent handoffs and baseline comparison; Azure recovery/observability; production approval/provenance controls. Verify category selection mechanics before submission.

Public GitHub repository, English pitch/testing instructions, reproducible setup, data generation, tests, evaluation report, dependency notices, and working judge-accessible deployment. Keep deployment available through judging; obtain judging end date. Demo target 110 seconds, strictly less than two minutes, showing actual working UI. No unsupported performance or prize claims. Confirm creation-date eligibility and all required submission fields against official platform.

## Explicit exclusions and limits

No video ingestion, live tracking, speed/distance measurement, off-ball analysis, trained xG/pass difficulty/win probability, arbitrary chat, real season data, licensed clips, automatic broadcast synchronization, multiple overlay templates, voice cloning, or payment system. Historical cohorts are synthetic and visibly labeled. Real-feed deployment requires licensed data, adapter validation, security and load review, and production access.

## Review decision

User review of this written specification is required before writing the detailed implementation plan. Implementation follows plan review and execution-method selection. No source code has been created by this specification.
