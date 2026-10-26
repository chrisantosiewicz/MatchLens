# Synthetic corner context

Owner authorization: “Great let's do that it's synthetic data anyway”, following the proposal for corner/restart tags, timestamped positions of all players around delivery, first contact and outcome. Execute this focused extension in the existing checkout. No additional infrastructure, video recognition, paid tier, or extra agent is authorized or needed.

## Intent

Answer who occupied the box, how their observed positions changed, who made first contact, and what followed a corner. Provide tactical context through observable occupancy, delivery and movement, rather than asserting passer intention or space creation.

## Approach

Use a new `corners` synthetic scenario layered on a seeded complete event match. Replace three whole 30-second possession blocks with explicit corner sequences, retaining normal play elsewhere. Existing shift/null/sparse fixtures remain unchanged apart from optional schema defaults. Generate four synchronized all-active-player frames per corner: setup, delivery, first contact, outcome. This implements the snapshot approach already discussed and accepted. Continuous tracking would add volume and interpolation assumptions without helping this demonstration; event-only corner tags cannot answer simultaneous occupancy.

Implementation choices left to the builder: schema/model names, exact scripted scenario times and players, seeded legal coordinates, local rendering and compact responsive styling. Keep the current Python/FastAPI and React stack; no dependencies. Work in the existing checkout to preserve the running local workflow; do not require an extra phone approval for routine reversible implementation choices.

## Evidence contract

- New optional set-piece event metadata identifies corner, sequence ID and phase. Model-level coordinates remain ball-event coordinates.
- A separate simulated position frame has an ID/revision, exact clock, anchor event ID/revision and all active player positions plus ball location. Never fill unobserved player positions from their last event.
- Use roster and substitutions to determine the active 22 players. Reject duplicate, missing, foreign or inactive players and mismatched timestamps/revisions; old fixtures simply have no positional evidence.
- Clip all events and frames at the selected clock. No future first contact/outcome, future positions or interpolation. Before delivery, display setup only.
- Counts use the attacking-direction-normalized penalty-area boundary and distinguish attackers from defenders, including goalkeepers in defender counts with an explicit label.
- Frames are sparse snapshots; position changes are observed endpoints, not continuous trajectories, speed, pressure or a causal explanation of runs.
- A named recipient or actual first contact does not prove intended target. Do not label another player an available/unmarked option based only on occupancy. No assertion that a runner dragged a defender or created space.
- Corrections to anchor events invalidate dependent frames. Source version includes positional revisions/content in corner scenarios. Position updates have no public write route.
- Synthetic labels and template/model/fallback labels remain visible. Model calls remain opt-in and budgeted, using the existing canonical selector for valid supplied summaries if wired into questions; no new agent or checker chain.

## Product

Add a corner section in the analysis column when the current fixture contains corner data. Select a visible corner and one available phase. Show a schematic pitch with 22 numbered markers and the ball, occupancy counts, delivery/first-contact/outcome sequence and a short evidence-grounded explanation. Selecting a player uses the existing player panel. Explain why a count is unavailable rather than rendering zero. English and Spanish support. This is simulated positional context, separate from the existing action map and illustrative video scene.

Local explanation should follow the owner's action → development → outcome cadence. Example claim shape: “[Team] has five attackers in the box at delivery. [Player] moves from outside the box at setup to inside at delivery. The delivery reaches [zone]; [actor] makes the recorded first contact, followed by [visible outcome].” Every match claim names supporting frame/event IDs and revisions; labels for general concepts remain separate.

## Acceptance

Deterministic seeds, valid direction/roster/geometry across 20 seeds, no goalkeeper corner deliveries or shots, no overlapping replaced possessions, bounded movement between keyframes. Correct counts from manually specified positions, direction mirroring, penalty boundary cases, no stale/partial frames, no future leaks, correction invalidation, graceful old-feed absence. Regression frontend coverage for rewinds, phase selection, failed refresh and source mismatch. Full backend/frontend checks, local browser QA and documentation of actual behavior. Public deployment and any live-model verification are separate recorded milestones; do not claim them from a local build.
