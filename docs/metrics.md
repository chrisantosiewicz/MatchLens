# Metric definitions and boundaries

All metrics describe fictional event data. No tracking measurements are inferred.

- A box entry is a completed pass/carry starting outside and ending inside the attacking penalty area: x >= 88.5m, y within [13.84,54.16], on a 105x68m pitch after directional normalization.
- Route labels use the final entry endpoint in attack-oriented lateral thirds. Both axes rotate when direction reverses.
- A progressive pass is complete, starts outside the box, and reduces Euclidean distance to goal centre by at least 10m. This is a prototype definition, not a claim of provider equivalence.
- Recorded involvement counts on-ball actions in the feed, excluding substitutions/stoppages. It is not touches or off-ball contribution.
- Comparison windows: before [anchor-10min,anchor), after [anchor,min(anchor+10min,viewer clock)]. Clip before to period start and mark incomplete windows provisional. Five entries in both windows are required for pattern wording; no statistical significance or causal claim is made.
- Player minutes assume generated 45-minute halves. Substitutions delimit active intervals. Real stoppage-time handling needs additional metadata.
- Percentiles use synthetic season rates per90, same broad position, minimum 900 minutes, all five fictional competitions. N includes the selected player. Midrank = 100*(lower+0.5*equal)/N. Suppress below 30 eligible peers or when selected player is ineligible.
- Match counts are separate from season rates and percentile bars. No percentile is computed from a partial match.
- Moments select goals, personal shots, qualifying actions preceding a shot, recoveries/tackles, and losses followed within 20s by an opposition shot before a recorded own recovery. Temporal association is not causal attribution.

The demo generator is reproducible but not empirically calibrated. It scripts baseline entry opportunities, increases right-channel opportunities after a fictional substitution in the shift scenario, and lowers shot probability to avoid treating every box entry as a shot. There is no hidden storyline field in analysis events. Held-out seeds remain necessary before a final accuracy claim.


October 21 corrections: zero-duration windows always contain zero actions, entries and evidence. Sparse observations are sampled independently from complete null-scenario ground truth; substitution metadata is retained to preserve roster intervals. Sparse counts are observed lower bounds and missing goals can make the observed score incomplete. Season shooting/progression and match pass-success probabilities depend on position; all ranges are heuristic, not calibrated. Failed passes terminate generated possessions. The five-entry sample gate is editorial only; it is not a hypothesis test or evidence of causation.
