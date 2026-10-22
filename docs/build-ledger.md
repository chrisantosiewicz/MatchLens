# Build ledger

Specification and native implementation approved by user on October 20, 2026.

Ruling: Work directly in the new project directory and initialize a local repository; there was no existing repository/branch to isolate. Cost if wrong: move the checkout later.

Ruling: Cloud integration stays deferred as requested during tooling setup. Local operation, tests, and truthful AI fallback precede account-dependent deployment. Cost if wrong: integration defects discovered later; preserve adapter boundaries.

Preflight: project contains only approved design/plan documents. No baseline source/tests existed. Event clocks, revisions and evidence IDs are the shared contracts. Tasks execute natively with per-milestone verification.

## Local vertical slice

- Tasks 1–3: generator, independent analytics fixtures, SQLite revision store, season percentiles, player moments implemented. Initial 17 tests passed; later regression cases cover plausible demo shot volume, same-time sequence ordering, and temporal turnover moments.
- Task 4: React/Vite local workspace and FastAPI routes implemented. Browser reached the application after running local servers outside the sandbox. Player markers, lineup, profile bars and template questions were inspected.
- Early Task 5/6 UI affordances are explicitly deterministic templates, not AI or durable publication. Task 4 is not a claim of completing the entire plan.
- Reviewed initial local slice with a fresh read-only reviewer. Fixed stale snapshots on seek, late recap responses, player-panel remounting, and shot attribution. Added regression tests observed failing before fixes.
- Ruling: Add practical template questions/recaps before cloud agents to make the local interaction reviewable. Cost if wrong: replace API internals; retain response provenance and explicit generation mode.
- Ruling: Use period-relative time with 45-minute half offsets for the current generator; do not claim stoppage-time-calibrated playing time. Cost if wrong: extend metadata for real feeds later.
- Ruling: Keep cloud account setup external to source implementation. User confirmed no Azure/Foundry account setup yet. No paid resources created.
- Minor (deferred): the installed Starlette TestClient emits an httpx deprecation warning; requests and tests pass. Review dependency compatibility before CI freeze.
- Minor (deferred): full Spanish UI terminology/bilingual review, pitch sequence animation, production auth, keyboard tablist arrow navigation, and public deployment are not complete.

- Task 5 partial: provider-independent bounded specialist workflow and opt-in Foundry adapter implemented. Scripted tests cover tool selection, revisions, rejection, timeout and factual fallback. No live model evaluation or Agent Framework SDK use claimed.
- Ruling: Producer currently selects canonical fact sentences rather than freely rewriting facts. Cost if wrong: language flexibility is reduced; a richer claim parser and evaluation are required before relaxing validation.
- Local browser validation: player moments changed the pitch to a supporting sequence; player questions returned event counts; English/Spanish recap respected selected clock; mobile and desktop layouts inspected. Saved screenshot at artifacts/matchlens-local.png (ignored by Git).
- Remaining external prerequisite: user confirmed Azure/Foundry not set up. No deployment, public repository, demo video, or competition submission has occurred.

## Verified local milestone (October 20, 2026)

- Backend: 28 passing tests. One upstream Starlette/httpx deprecation warning remains, recorded above.
- Frontend: 9 passing tests; TypeScript and Vite production build passed.
- Ruff lint and format checks passed; Git diff whitespace check passed.
- Follow-up review found Spanish moment-label and model/template disclosure defects. Added failing regression tests, fixed both, and reran frontend tests/build.
- New workflow provider and API integration are covered by scripted tests only. Actual Foundry behavior, latency and quality remain unverified.
- Local preview: http://127.0.0.1:5173. No paid or public resources created.
- Next milestones: cloud account/project setup and SDK smoke test; richer agent evaluation; persistent approval/publication and synchronized overlay; complete localization and accessibility; deployment and submission.

## Seamless companion refinement

- User reported flashing at every replay tick. Reproduced with a delayed-response regression: strict snapshot-key gating removed all visible data between forward updates. Retain confirmed snapshots only when their clock is not ahead of requested time; rewind guard remains intact.
- Both-team action map defaults to trailing two minutes, max12 actions. Removed central empty-state text; empty pitch remains quiet. Older actions leave visualization only, not analytics storage.
- Added exact-time recap with latest goal attribution, recorded goal-sequence involvement, and uncapped qualifying moment count. Timestamped recap and player answers remain readable during forward playback; rewind hides future answers/recaps.
- Added Watch/Explore preview, synthetic numbered roster markers, substitution-aware active entities, milestone cards and player deep links. Explicitly an illustrative synthetic SVG scene, not video recognition or an encoded video.
- Ruling: Initial action cap12 and milestone thresholds4/8/12… are provisional interaction policies, not football significance claims. Cost if wrong: adjust density/cooldown after real viewer tests.
- Follow-up read-only review identified disappearing recaps during play; added failing test and fixed clock-safe retention.
- Verification: 31 backend tests, 15 frontend tests, production build. Backend TestClient deprecation warning remains. Source guidance: docs/watch-companion.md. Paid/cloud/video-recognition work remains unimplemented.
- Browser verification: Watch layout rendered; forward playback retained the player panel; a generated recap at70:00 named the last goal at54:52 and recorded non-involvement; advancing the clock through71:07.5 produced Mateo Silva's actual 32nd progressive-pass alert. Screenshot: artifacts/matchlens-watch-layout.png.


## October 21 — judging review recovery and live contract investigation

- Created root AGENTS.md and prioritized submission checklist; registration confirmed, Foundry resource/project/model now supplied by user. Secrets/config remain ignored.
- Fixed synthetic sparse-team sampling, position-sensitive completion/season shooting/progression, failed-pass possession termination; regenerated fixtures and measured 20-seed sanity ranges (docs/data-validation.json).
- Fixed trusted requested-answer fallback, empty zero-duration windows, bilingual shooting/causal relevance and configuration-vs-connectivity reporting.
- Installed/locked optional Foundry SDK. Tenant-specific authentication produced real model output/usage. Structural validation rejected initial unsupported numeric tokens. Added exact Decimal equivalence, restricted numeric sources, strict JSON output schema, subject/window guides, rejected-candidate diagnostics and provider call accounting/lifecycle.
- Initial 20-case x3 policy experiment made 45 calls (45,309 input / 1,839 output tokens). Developer review found semantic/time errors despite structural acceptance; no quality gate claimed. Default single policy now leaves direct counts deterministic; specialist remains experimental. Fresh review caught runner/API routing mismatch; shared helper + regression fixes it. Current-policy live rerun remains pending successful reauthentication. Fresh-seed process was stopped after authentication failures; no passing fresh acceptance artifact exists.
- Connected canonical SQLite revisions to read APIs and token-protected synthetic ingestion. Regression verifies corrected pass updates stats, alert, answer and recap; duplicates do not inflate. Previously displayed answers/recaps are not auto-retracted; correction-notification stream remains a limitation.
- Added loopback built-demo launcher and same-origin static serving. HTTP smoke verified HTML/assets/state/template question. Public paid-model access controls, hosted judge access, repository publication/license and demo video remain unfinished.
- Verification: 47 backend tests pass; 15 frontend tests pass; production build passes; Ruff lint/format and git diff whitespace checks pass. Read-only fresh review found one consequential eval mismatch, now fixed with test. No live semantic reliability or independent bilingual/user evaluation claimed. Azure-specific dollar cost remains unknown; token usage is recorded.


October 21 retry after user requested renewed sign-in: successful authenticated fresh-seed calls for seeds 303/404, English/Spanish, all four structurally accepted. Development inspection still found misleading unequal-window interpretations; semantic acceptance remains false. Measured calls recorded in foundry-fresh-verification.json; full local context/output in ignored artifacts/foundry-fresh-check.json. No broad reliability or independent bilingual validation claimed. Next: supply explicit duration-normalized rates and enforce temporal-comparison constraints before another semantic acceptance check.


## October 21 evening — local recovery verified

- Fresh full verification: 54 backend tests, 19 frontend tests, Vite/TypeScript build, Ruff backend/scripts and packaging unittest pass.
- Rapid seeking exposed parallel SQLite cursor interference. Concurrent read/correction regression reproduced invalid JSON; locking reads as well as writes fixed it.
- Canonical source versions now prevent mixed UI snapshots and invalidate old answers/recaps when a correction is observed. No background correction stream.
- Comparison cards disclose actual durations; rates rather than raw counts determine unequal-window direction. Active player minutes and a checked rate contract enter optional model context. New contract has scripted regression coverage, not fresh live acceptance.
- Explore scene preview now uses document flow so it does not cover recap controls.
- Added process-local model request budget (6/minute, 50/session defaults); not distributed protection or a dollar ceiling.
- Official Azure Retail Prices meters yield conditional initial-experiment estimate USD 0.021066 assuming Global Standard. Actual deployment SKU/bill/credits remain unverified. See price-reference.json.
- Public GitHub repository created; final source/package/video publication in progress. No public hosted application or semantic quality acceptance claimed.

- Final independent review reproduced zero-duration fallback counting at the exact anchor and signed-number validation stripping minus signs. Added failing regressions, fixed both; full backend 54 passed afterward.

- Clean extracted ZIP independently installed locked backend/frontend dependencies, passed 54/19 tests and built. Initial npm audit found development-only Vitest/tinypool advisories; upgraded Vitest to 4.1.12, reran all 19 frontend tests/build and audit: zero reported vulnerabilities (including development dependencies). This is a dated registry audit, not a security certification.
- Created and decoded 105-second captioned edited screenshot walkthrough; all seven sections visually inspected. Not continuous interaction/video-recognition evidence.


## October 21 — authenticated current-policy evaluation and hosting preparation

- Successful renewed Foundry sign-in; completed identical 20-case template/single/specialist comparison on d814db3. See evaluation-current-results.json. Single: six calls, four structurally accepted, one abstention, one fallback; specialist: forty calls. Semantic developer review still found inaccurate subject wording and unsupported area-presence descriptions; no final acceptance or independent bilingual review claimed.
- Reproduced range-parser false rejection (50-60 minutes interpreted as negative60), fixed without accepting genuinely unsupported signed values. Seven explanation tests and all54 backend tests pass; Ruff passes. Tightened prompt to distinguish all recorded actions from passes and exclude internal field names/area-presence inference. Revised prompt not yet live-accepted.
- User authorized free-tier hosting only. Added package_hosting.py: exact locked production dependencies, Python source and frontend assets only, credential-pattern check, no environment or caches. Extracted20-file hosting archive independently passed HTML, hidden environment, health/template, state, player, comparison, question and recap checks.
- Azure management interactive sign-in timed out after300seconds; no subscription/resource discovery or hosting provisioning completed. No paid plan created. See deployment.md for precise runtime/startup/configuration and acceptance checks.


## October 21 — public free-tier deployment verified

- Renewed Azure management authentication succeeded. Registered Microsoft.Web. North Central US F1 creation rejected for zero quota; West US3 requested F1 succeeded, Azure returned LinuxFree/U13. Created app matchlens-chris-demo-2026 with template mode, HTTPS, disabled FTP and one worker; no paid tier enabled.
- ZIP deployment completed. Anonymous public checks pass HTML/assets (hashes match local build), .env404, template health, match/player/comparison/question/recap and source revision consistency. Browser player question and recap verified. Evidence: hosting-verification.json and ignored artifacts/matchlens-public-preview.png. No uptime/load-testing claim.
- ARM read verified model deployment GlobalStandard, gpt-4.1-mini version2025-04-14. Retail usage estimates remain estimates, not bills.
- Fresh prompt check seeds505/606 made six calls: five structural explanations, one abstention. Developer reviewed four supported explanations, one Spanish failure and one appropriate abstention. Overall semantic quality remains unaccepted; independent bilingual review absent. See foundry-current-verification.json. Public demo remains template-only.
