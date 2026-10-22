# Football meaning: where your judgment helps

These are editorial questions for the owner, not blockers or claims that the event feed establishes intent. You can respond to any row with a concrete example and wording you would trust on air. Default: describe recorded contribution and uncertainty; do not rate decision quality.

| Situation | What the feed can establish | Where your input helps | Needs more than events? |
| --- | --- | --- | --- |
| Safe connecting pass before a shot | Player touched the recorded same-team sequence before an attempt | When is this worth highlighting rather than routine involvement? How far back should credit extend? | Judging available alternatives/pressure needs tracking/video |
| High completion, little progression | Completed/attempted passes and progressive counts | Preferred wording: reliable circulation, limited forward contribution, or neutral description? No automatic praise/blame | Intent and whether a safe choice was correct need more context |
| Progressive pass, then turnover | Advancement followed by observed loss in that sequence | When should the story emphasize territorial gain versus an unconverted attack? | Chance quality/decision quality not established |
| Turnover, then opposition attempt | Recorded ordering and elapsed gap | How prominent should the alert be? Wording that avoids assigning sole blame? | Pressure, team support and responsibility need tracking/video |
| Low involvement | Few recorded touches/actions, with active-minute baseline | When is silence meaningful to fans? Should the product simply offer “not much recorded involvement”? | Marking, decoy runs and off-ball value require tracking |
| Substitute has no before baseline | Entry time and subsequent contributions | Compare with team before/after, role replacement, or only describe their own contribution? | Replacement-role equivalence cannot be assumed |
| Player trend differs from team trend | Calculated rates move differently | Which contrast feels editorially useful versus a trivial short-window fluctuation? | No causal substitution claim |
| Many box entries, few shots | Recorded sequences reach box without attempts | Preferred wording for access without attempts; minimum sample before surfacing it? | Finishing opportunity and threat quality need calibrated models/video |
| Late lead versus chasing a goal | Recorded score and clock for a complete feed | How should significance change with game state without inventing intent? | “Protecting a lead” is intent unless directly evidenced |
| Recovery followed by attack | Recorded recovery and subsequent same-team sequence | What chain length/time limit feels meaningful? Does it merit a spotlight? | Winning duel difficulty and pressure unobserved |
| Sparse or corrected feed | Missing-observation flag/revisions | Useful wording when the product should withhold a story | Cannot infer absence from missing events |
| Fan versus analyst language | Same verified facts and sequences | How much detail, terminology, and caution should each audience hear? | Editorial preference, not extra data |

Implemented first: same-team shot build-up, progressive-pass sequence ending in turnover, and selected-player turnover followed by an opposition shot within20seconds. Each exposes complete source events and a limitation. Thirty-second build-up and20-second transition windows are editorial heuristics, not validated football thresholds. Progressive-pass/entry definitions remain the documented deterministic metrics.

Start with the first four rows. Your examples can improve story selection and language; they will not be used to pretend that unseen pressure or intent was measured.

## Owner feedback applied — location-editorial-v1

Action origins/destinations are normalized by attack direction. Backward means at least5m toward own goal along the pitch; own-half/final-third and Euclidean pass length are explicit geometric facts. They are event locations, not tracked player positions. Five completed backward passes making up at least half the completed passes in the selected interval qualify for descriptive recycling language. This does not establish intent to manage tempo.

Shot build-up credit is limited to the last three completed passes within30seconds of a same-team shot. The card exposes exact rank, measured origin/destination/distance and all intervening recorded events. A deep pass into the final third retains this credit even if it is not the final pass. No line break, through-ball class or assist is inferred.

Progression-loss stories name the actual turnover actor and intervening action count. Repeated immediate outcomes require at least3sequences in the last10minutes for a spotlight; this does not diagnose risk-taking or poor receiver control. Turnover/opposition-attempt cards expose origin zone and whether zero/one on-ball actions intervene; later shots do not imply sole responsibility. Regained possession and stoppages cut the linkage.

Same-metric player/team entry contrast: two complete10-minute windows, full player exposure in each, at least5player entries combined and absolute player-count difference>=3, plus opposite directions. Counts/durations/rates remain inspectable. This is a starting editorial policy, not validated significance. No before exposure remains unavailable rather than zero; replacement name/listed position is shown without claiming tactical equivalence or substitution causation. Positions never impose a ceiling on attacking impact.

Box access counts distinct explicitly completed entry possessions in the last15minutes; unfinished or ambiguous groups are excluded. Spotlight gate: at least8completed entry possessions and at most1followed by a same-team shot. Recovery stories require a same-possession box entry/shot within20seconds and five subsequent on-ball actions. Late starts75:00 and only complete visible goal records provide game state. Incomplete feeds suppress these conclusions. Existing revision checks withdraw stale narratives and reject mixed source versions.

Low involvement uses <=3recorded on-ball actions over at least15active match minutes as a conservative provisional gate; it says limited recorded on-ball involvement, never no overall influence. Fan and analyst share all eligibility gates and material limitations; analyst adds denominators/source details.

Still useful from you: examples of backward circulation you consider worth a spotlight; whether the3-sequence immediate-loss gate is too noisy; and examples where even third-last-pass credit feels too remote. These will refine editorial selection, not authorize inferred defensive lines, intent or unobserved supporting players.

Fan interpretation now uses the concise story (moment, meaning, limitation); analyst mode retains calculation detail. Direct pass-count questions keep their direct numeric answer. Both modes retain identical structured evidence and policy gates.
