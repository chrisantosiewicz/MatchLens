# Owner editorial review — October 25, 2026

Qualitative product-owner feedback collected in chat. This is not independent or blinded evaluation, a viewer study, a model score, or evidence of market demand. Decisions below are editorial requirements pending implementation and regression verification; saved execution records remain unchanged.

## 1. Earlier sideways pass before a shot

Recorded case: `attack-fan` in `evaluations/viewing-guide-v1.json`, selected clock 70:00. Mateo Silva's lateral pass at 69:07 (`match-7-shift-e710`, revision 1) precedes two further completed passes and Nico Vega's saved attempt at 69:22 (`e713`). The action advances 0.83m longitudinally and is not a progressive pass.

Owner rejected automatic highlighting of this earlier pass. A non-progressive pass may matter, but this event feed does not establish that it created space. Owner agreed to distinguish automatic sequence inclusion from selective creative credit:

- Always retain the final pass before a shot in the recorded sequence. Use “final pass before shot” for this saved attempt; do not invent a goal assist.
- Normally feature the second-last pass. Short distance alone is not sufficient reason to remove it from the sequence.
- A short second-last pass entering the penalty area may still earn a highlight; owner explicitly agreed.
- Earlier passes remain available for player exploration. Routine sideways participation alone does not trigger an automatic broadcast alert or establish chance creation.
- Treat “build-up contribution worth inspecting” as a proposed presentation label, not a calibrated probability or proof of influence. Creating space, beating pressure and defensive disruption require additional evidence.

Still to define before implementation: short-pass threshold, additional independent highlight triggers, timing/possession bounds, and how to avoid rewarding any early touch solely because a later shot occurred. No empirically validated threshold was supplied.

## 2. Recovery followed by a box entry — accepted editorial direction

Recorded guide case `defend-es`, seed 5227, player `harbor-6` (Theo Marin II), selected clock 70:00. Sequence `recovery_followed_by_attack:match-5227-shift-e542:match-5227-shift-e546`: recovery in defensive third at 51:31, three completed passes, then Nico Vega II's completed pass into the penalty area at 51:46. No shot is included in this selected sequence. It supports descriptive recovery-to-box-entry participation, not an inferred counterattack, defensive pressure or sole creative credit.

Owner explicitly stated that a shot is not required and accepted moving on after a recovery-to-attack highlight was proposed. Editorial direction: recovery, continued player involvement and a subsequent box entry can qualify without a shot. Still subject to complete coverage, sequence/time bounds and source verification; this is not an empirically calibrated rule.

Preferred cadence: action → build-up → concrete outcome, in natural football language. Proposed wording: “Marin recovers the ball and begins the build-up, exchanging passes with Moreno before finding Vega, whose next ball takes the attack into the penalty area.” Owner initially used “creates a chance in transition”; retain the cadence without publishing those mechanisms where only the box entry is established. Implementation and tests remain pending.

## 3. Team entries increase; selected player has no direct entries — pending

Recorded guide case `neutral-analyst`, seed 5227, Theo Marin II at 70:00. Harbor has 5 box entries from 50:00–60:00 (end exclusive), 6 from 60:00–70:00 (end inclusive); equal ten-minute windows, rates 0.5 and 0.6 per minute. Marin has 0 direct box entries in both windows and ten active minutes in each. These metrics do not measure earlier build-up involvement or establish an improvement, deterioration, substitution effect or cause. Owner judgment pending.

Owner rejected the proposed count-only explanation as weak and asked to trace the actual sequences and identify the question the statement serves. Intended question: “How is Marin involved in the team's moves into the penalty area?” Team entry totals alone cannot answer that.

Developer investigation regenerated seed 5227, restricted events through 70:00, identified the same 11 entry event IDs as the recorded comparison, and inspected each same-period possession through its entry. In the 50–60 window Marin performed recorded actions before 2 of 5 entries: e546 (recovery e542 and passes e543/e545), e581 (recovery e577 and pass e578). He was also the named recipient of entry e564, and of e581; receipt is a separate role, not an additional authored action or evidence of a controlled touch. Thus authored build-up participation is 2/5, whereas authored-or-named-recipient participation is 3/5; do not conflate them.

In the 60–70 window he completed earlier build-up passes in 4 of 6 entry sequences: e634 before e636; e668 before e669; e701 before e702; e721 before e723. All IDs have prefix `match-5227-shift-`, revision 1. All four sequences start with a recorded team recovery and contain no intervening opposing touch or failed pass before entry. Example: Marin passes to Luca Moreno II at 67:41 (e701); Moreno's next completed pass reaches Rafael Cruz II in the area at 67:46 (e702).

These are descriptive sequence-participation counts, not creative quality, causal influence, off-ball contribution or a validated trend. Proposed response should lead with the viewer's question, identify Marin's recorded role, give one concrete sequence, and make totals supporting context. Final owner judgment and product implementation remain pending.

Owner further requested tactical meaning and themes, including following actions in the final third. A second developer inspection followed all four 60–70 entry possessions to their visible ending, through the same selected 70:00 clock:

| Entry | Marin's earlier pass | Subsequent outcome |
| --- | --- | --- |
| e636, 60:46 | e634, 60:37: middle third, own half → opposition half; 11.4m longitudinal gain, progressive | Morel II shot wide at 60:52, e637 |
| e669, 63:46 | e668, 63:41: lateral 0.35m pass in own-half middle third; not progressive | Cruz II turnover at 63:52, e670 |
| e702, 67:46 | e701, 67:41: middle → attacking third; 16.78m longitudinal gain, progressive | Cruz II turnover at 67:52, e703 |
| e723, 69:46 | e721, 69:37: defensive → middle third; 17.39m longitudinal gain, progressive | Diallo II turnover at 69:52, e724 |

All IDs retain prefix `match-5227-shift-`, revision 1. Three of the four authored passes qualify as progressive under the existing metric. One is an extremely short synthetic pass: retain factual participation but do not give all four actions equal editorial importance or treat this as an empirically realistic benchmark. This is a potential data-quality case to validate, not a licence to silently modify the recorded feed.

Proposed tactical interpretation: Marin is a more frequent recorded link in progression towards box access in these windows; his contribution includes moving play between thirds rather than delivering the final entry. The sampled attacks reach the area but three of these four end in a recorded turnover; one ends in a wide shot. Do not call all four chances created, infer pressure/space/defensive shape or attribute the later losses to Marin. “Doubled” applies only to authored involvement in box-entry sequences (2 → 4), not total contributions, ability or tactical impact.

Proposed future analysis should distinguish the player's action role, entry route/location and what follows (shot, continued possession, recycle, turnover) with exact evidence and clock bounds. These are design notes; no new tactical detector, template or model prompt has been implemented or evaluated during this owner review.
