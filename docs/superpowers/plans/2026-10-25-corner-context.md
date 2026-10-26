# Synthetic corner context implementation plan

> **For agentic workers:** Use superpowers:executing-plans to implement task by task in this session. The user has authorized execution; no additional design-selection round is needed for the snapshot approach just approved.

**Goal:** Explain corner occupancy and recorded movement with explicit synthetic position evidence.

**Architecture:** Optional positional frames and restart metadata accompany a separate seeded corner fixture. A deterministic corner analysis endpoint clips to clock, validates frames against events/active roster and renders EN/ES summaries. A responsive React component displays the synchronized frames alongside existing analysis.

**Tech stack:** Existing Python 3.12/Pydantic/FastAPI, React/TypeScript/Vitest; no new dependencies.

**Spec:** docs/superpowers/specs/2026-10-25-corner-context-design.md

## Global constraints

- Explicit synthetic positional evidence only; no inferred tracking from event locations.
- Selected clock/source revision everywhere; omit unavailable counts/outcomes instead of zero or guesses.
- No inferred intention, unmarked options, pressure, space creation, continuous paths or speed.
- Preserve current fixtures and local demo; public model calls stay disabled.

## Review focus

- Snapshot missing a defender must not undercount the defence.
- Corrections to a delivery cannot leave a valid-looking old occupancy frame.
- Selecting an older phase cannot expose an outcome beyond the viewer clock.
- Direction switching must count the correct penalty area.
- A delayed frontend response after rewind/source correction must never render stale positions.

## Task 1: Data and evidence engine

Files: backend/matchlens/models.py; new corner_data.py and set_pieces.py; synthetic.py; backend/tests/test_set_pieces.py.

Interfaces: `generate_match(seed, 'corners')` produces a fixture with optional `position_frames`; `corner_context(match, clock, language='en')` returns visible corner cards, exact phase frames, occupancy, evidence IDs/revisions and local narrative.

- [x] Add failing tests for corner generation, independently expected occupancy, missing/duplicate/incorrect roster, mirrored direction, selected clocks and corrected anchors.
- [x] Run tests and confirm missing functionality; implement minimal schema, seeded generator and fail-closed analysis.
- [x] Validate 20 seeds, four phases per corner, active substitutions, coordinate bounds and movement distances. Preserve historical fixture behavior.

## Task 2: API and question integration

Files: backend/matchlens/api.py; tests/test_set_pieces.py; existing question pipeline only where needed.

- [x] Add failing API tests: scenario discovery, positional-context route, source consistency and no future frames/outcomes.
- [x] Add fixture and labels; extend source-version input only for positional fixtures. Serve `/set-pieces` with selected-clock bounds and source version.
- [x] Make corner questions return the grounded corner summary with a useful local result; optional existing selector may choose canonical explanations only, no new role.
- [x] Verify no changes to model budgets or anonymous cloud access.

## Task 3: Fan-facing view and release verification

Files: new frontend/src/components/SetPiecePanel.tsx and .test.tsx; contracts.ts; App.tsx; styles.css; README, STATUS and spec status.

- [x] Write failing frontend tests for correct counts, phase selection, unavailable data and rewind/source-response invalidation.
- [x] Add a small component receiving match/source/clock/language/player and onPlayer; keep it separate from action-event map. Explain sparse snapshots and show evidence details.
- [x] Run backend, frontend, Ruff and production build checks. Review changes, browser-test local English/Spanish and rewind, save proof screenshot.
- [x] Record actual checks and limitations. Preserve historical Foundry runs and label current corner output as deterministic until separately verified.


Execution record: implemented in the existing checkout under prior authorization. Ruling: corner explanations stay deterministic; no additional model role or paid evaluation is needed for occupancy facts. Automated recap integration added with a selected-clock regression. Read-only review findings were reproduced and fixed; full local verification is 139 backend / 35 frontend tests, Ruff and production build. Azure management authentication expired; phone device sign-in initiated for optional public rollout. No public rollout is claimed without anonymous verification.
