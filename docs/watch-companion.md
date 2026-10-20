# Watch / Explore companion refinement

User direction, October 20, 2026: complement a match broadcast rather than replace it with a dashboard. Demo source chosen: synthetic match video.

## Layout implemented for review

- Watch: illustrative synthetic scene in the main column, player panel at right, compact recent-action map and clock below.
- Explore: existing analysis workspace; small synthetic-scene picture-in-picture with return-to-Watch control.
- Player/alert clicks select the stable player ID and open Explore. Synthetic roster identity includes team and number; substitutes replace active IDs at their event timestamp.
- Progressive-pass milestones: every fourth pass from count 4, only players ranking in top two at the triggering event; one recent card at a time, 12-second match-clock lifetime, dismissible. The secondary player's actual rank/count is supplied; it is not assumed to be second. This threshold/cooldown policy is provisional.
- Default map: both teams, current period, trailing 120 seconds, latest 12 spatial actions. Full history is retained for recaps and metrics. Team filters are independent from analysis-team selection. Twelve is a starting visual-density choice, not a user-research finding.

## Important boundary

The new scene is an SVG-based synthetic layout/interaction preview, not an encoded video file or computer-vision output. Illustrative off-ball positions are fabricated from formation defaults, supplemented by available recorded action locations. They are not measured tracking positions. True synthetic video rendering/export and OCR/reidentification remain future work.

A real video-recognition pipeline would need jersey detection/OCR, team/roster resolution, temporal tracking across occlusions and camera cuts, confidence/unknown states, and explicit substitution handling. The present event data's player ID is authoritative; no recognition accuracy is claimed.

## Seamless playback

Previously each request-key change hid all current data until replacement arrived. Forward clock ticks now retain the last confirmed snapshot and update in place. Backward seeking still suppresses future snapshots. Older facts remain identified as updating while requests are pending. Player answers and recaps carry their source minute and persist forward, but are hidden on rewind/context changes. No central empty-pitch overlay flashes between requests.

## Recaps

Recaps identify the selected clock, latest goal minute/scorer, selected player's participation in the recorded goal sequence, completed passes, shots, uncapped qualifying-moment count (or none), and a short event-based summary. Lack of recorded involvement is not a claim about off-ball contribution. Counts are not restricted to the five moments displayed in the panel.

## Candidate next features (not implemented)

1. Quiet/standard/analyst notification levels and a recent-alert shelf.
2. Follow-player pin with an explicit substitution handover choice.
3. Expandable “why this alert” combining the source action and synthetic season baseline, with small-sample caveats.
4. Manual video/event-clock calibration and a clear live-versus-inspecting state.
5. Alert density control, then test 8/12/16 actions on small and large displays.
