# Synthetic positional context for corners — October 25

Implemented a separate **Corners · simulated positions** scenario. Choose it in the match selector, then use **Who occupies the box**. At the default 70:00 clock three corners are visible: setup at 20:01, 62:31 and 64:01; deliveries at 20:04, 62:34 and 64:04. Each has setup, delivery, first-contact and outcome snapshots, with 22 active players and a ball position. Click a numbered player to inspect the existing player profile.

## What it establishes

- Deterministic simultaneous counts in the attacking penalty area, separated into attackers and defenders, with defending goalkeepers explicitly counted.
- Observed outside-to-inside position changes between setup and delivery, for players present in both frames.
- Delivery, first contact and following shot or pass, when those events are visible at the viewer's selected clock.
- English and Spanish local narratives; optional models are not used for corner answers. The existing analyst/guide remains available for other supported questions.
- Automated recaps append the latest visible corner summary and positional source IDs, without exposing later first contact or outcome.

For example, the scripted delivery has five attackers and eight defenders in the area, with three attackers outside at setup and inside at delivery. Jonas Berg makes the recorded first contact in the Northbridge examples; the Harbor delivery is met by an opposing player and followed by a completed pass. These are explicit synthetic scenarios, not empirical football findings. Seeds change small positional offsets and shot outcomes; the occupancy arrangements are scripted, not sampled from a calibrated tactical model.

## Data and evidence

`Event.set_piece` records a corner ID and phase. Ball-event locations retain their original meaning. Separate `MatchFixture.position_frames` contain simulated player positions, ball location, frame ID/revision, exact clock and anchor event ID/revision. Schema 1.1 is used for the corner fixture. Original shift/null/sparse event generation is unchanged; their serialized events now have the optional metadata default and their fixtures the empty positional-frame default. Historical source hashes and recorded Foundry trials remain historical and have not been rerun for this extension.

The generator replaces three complete thirty-second possession blocks in a seeded null match; it does not superimpose contradictory normal play and corner events. Scores are recalculated, and active lineups follow substitutions. The snapshots are sparse key moments, not continuous tracking, real footage or model-detected positions. Small synthetic offsets and movement checks do not establish empirical realism.

`GET /api/matches/{id}/set-pieces?period=2&elapsed_ms=1500000&language=en` returns only observed corner phases. Frame validity requires the exact active 22-player roster, unique IDs, matching clock/revision and an intact ordered phase sequence. Corrected anchors invalidate positional summaries. Unknown, missing, partial or stale frames withhold counts and positions instead of returning zero. A substitute absent from a frame receives no invented position or run.

Corner questions such as “Who was in the box for the corner?” describe the latest visible corner and selected player's delivery position if present. They are deterministic templates, explicitly labeled. Arbitrary tactical questions, intended targets, unmarked options, pressure, space creation, man-marking, defensive reactions, continuous trajectories and causal explanations are not established. General open-play occupancy is unavailable outside these explicit corner snapshots. There is no positional ingestion/write API.

## Verification and reproduction

```powershell
backend/.venv/Scripts/python.exe -m pytest backend/tests/test_set_pieces.py -q
backend/.venv/Scripts/python.exe -m pytest backend/tests --basetemp artifacts/pytest-corners -q
backend/.venv/Scripts/ruff.exe check backend
cd frontend
npm test
npm run build
```

Observed local results: 139 backend tests, 35 frontend tests, Ruff and production build passed. The corner test iterates 20 seeds, checking rosters, counts, bounded movement, direction, future exclusion and correction handling. Regression tests cover substitutions between snapshots, selected inactive substitutes, goalkeeper placement, incomplete follow-up passes, malformed or reordered contact phases, selected-clock recaps and UI withdrawal on detected source changes. The UI retains an explicitly timestamped older snapshot on a forward network failure and withdraws it on rewind or correction.

A fresh read-only reviewer reproduced the substitution and corrected-event wording defects. Both were reproduced in failing tests and fixed; the reviewer confirmed the fixes. Local browser verification covers scenario selection, full-player view, delivery/setup phase counts, Spanish output and withdrawal on period rewind. Public deployment is recorded separately. Zero model calls were made for the extension; no claim of new Foundry or model-quality verification.

To export a fixture without overwriting earlier recorded example data:

```powershell
backend/.venv/Scripts/python.exe -m matchlens.synthetic --output artifacts/corner-fixtures
```

Public hosting requires current Azure management sign-in; no new resource or paid tier is needed. Do not describe this extension as publicly deployed until anonymous checks verify it.
