# Best Use of Microsoft Foundry Project — MatchLens evidence

Recommended category; owner selection and submission remain pending. This page explains the implemented Foundry contribution, not a claim of category leadership. Evaluated product source: `802f154`. Recorded model trials have their own earlier source freezes and do not verify every subsequent change.

## The category case

MatchLens uses Microsoft Foundry to select which supported football interpretation and next investigation to present for a viewer's question, player and replay clock. Deterministic services calculate the facts, determine eligible claims and render their evidence. An optional analyst selects a canonical interpretation; an independently requested viewing guide ranks available actions. Neither role is trusted to invent match facts or verify its own prose.

This is bounded editorial selection integrated into a functioning football application. The current evidence demonstrates authenticated execution and inspectable decisions. It does not establish improved viewer understanding, faster development, broad reliability or scalable operation.

## Start here — no Azure account or model call needed

1. [Recorded analyst and guide](https://matchlens-chris-demo-2026.azurewebsites.net/evidence/guide.html): compare complete local/model lists and expand the request, catalog, actual outputs and usage. These are historical authenticated calls.
2. [Recorded canonical comparison](https://matchlens-chris-demo-2026.azurewebsites.net/review/?mode=execution): inspect candidates, selected output, role handoffs and failures.
3. [Raw canonical execution](evaluations/fair-canonical-v1.json), [summary](evaluations/fair-canonical-summary-v1.json) and [raw guide execution](evaluations/viewing-guide-v1.json): full retained records; independent human fields remain null.
4. [Final test package](https://github.com/chrisantosiewicz/MatchLens/releases/download/judge-evidence-2026-10-22/matchlens-judge-final-oct27.zip): current local corners and template operation, with English setup. The public app is the older October 22 build.

## One actual editorial decision

Historical case `5201-north-6`, viewer clock 70:00, question **“Why does this passing matter?”** Both policies had two eligible canonical candidates and the same source facts and rendering freedom.

| Policy | Actual choice | What the chosen sequence establishes |
| --- | --- | --- |
| Fixed deterministic ranking | Silva's progressive pass at 68:07; Vega turnover at 68:22 after two intervening actions | Recorded advancement and the subsequent sequence outcome; not blame or pass quality |
| Single Foundry selector | Silva's 31.92m pass at 52:07; Laurent saved shot at 52:22, with Silva third-last completed passer | Recorded build-up involvement beyond progressive-pass totals; not an assist, chance quality or causation |

Selected claim IDs: deterministic `story:progression_without_shot:match-5201-shift-e692:match-5201-shift-e695`; single model `story:shot_build_up:match-5201-shift-e538:match-5201-shift-e541`.

This demonstrates selecting an older recorded build-up over the more recent progression/loss sequence. The hypothesis is that this better addresses a viewer seeking a contribution missed by totals. It remains an **unvalidated editorial hypothesis**: no independent preference, comprehension advantage or superiority over the proposed relevance-aware baseline is established. Do not describe the historical fixed baseline as the newer baseline design.

## Measured execution and architecture decision

| Recorded trial | Observation | Practical boundary |
| --- | --- | --- |
| Guide trial | 8 calls: 1 analyst and 7 guide; all 7 guide lists used valid catalog IDs; broad clarification used 0 calls | Catalog validity is an engineering result, not usefulness |
| Guide latency and usage | Median guide response 1,355.72 ms; total trial 22,924 input / 431 output tokens | Developer-selected cases; no load test or independently measured cost |
| Fair six-case canonical comparison | Single selector: 6 calls, 4 model selections, 2 fallbacks; three roles: 16 calls, 3 model selections, 3 fallbacks | Same canonical freedoms; no demonstrated quality advantage |
| Recorded median exercised-case latency | Single 1,562.72 ms; chain 4,954.07 ms | Fixed order, one run per case; not a controlled general performance benchmark |
| Isolated checker probes | 5 flawed proposals accepted; 2 vetoed; 1 unresolved | Checker is not a reliable semantic safeguard; deterministic publication constraints remain essential |

The preferred controlled policy is the simpler canonical selector. The fair trial recorded ten fewer calls than the chain across the same six eligible cases. This is a measured request-count difference, not proof of equal quality, monetary savings or improved developer productivity. The guide is optional, has a distinct exploration role and does not add a mandatory call to every answer.

## What Foundry supplies versus what MatchLens supplies

| Boundary | Implementation / evidence |
| --- | --- |
| Foundry model access | Backend `AIProjectClient`, `get_openai_client()`, Azure identity, configured `gpt-4.1-mini`; actual authenticated outputs retained |
| Model decisions | Canonical conclusion ID and optional alternative IDs; guide's ordered 1–3 catalog IDs |
| Match facts and interpretation eligibility | Deterministic analytics, editorial gates, claim ledger and source revisions in MatchLens |
| Rendering and evidence trail | Server-authored claims/actions, event IDs/revisions, clock/source snapshots and visible generation-mode labels |
| Controls and fallback | MatchLens contracts, budgets, source checks and local templates; no assurance claimed from a model checker |
| Trial evaluation/records | Repository Python runners and saved JSON, not a claim that Foundry-native evaluation or tracing dashboards were used |
| Public hosting | Azure App Service older template build; not evidence of live public model calls or scale |

Source: [provider](../backend/matchlens/providers.py), [canonical selector](../backend/matchlens/canonical.py), [guide](../backend/matchlens/guide.py), [evaluation runner](../scripts/evaluate_guide.py), [fair comparison](fair-canonical-evaluation.md), [architecture](architecture.md).

## Submission paragraph

Microsoft Foundry powers MatchLens's optional evidence-grounded analyst and viewing guide. The analyst selects an eligible interpretation for a player and replay clock; the guide ranks available next investigations. Actual authenticated executions retain the supplied facts, candidates, model choices, usage and failures. A fair canonical comparison did not establish a three-agent benefit, so the preferred controlled workflow uses the simpler selector. MatchLens keeps statistics, evidence eligibility and publication checks deterministic, with useful template operation when cloud output fails. Recorded choices demonstrate operation; independent viewer benefit, incremental model usefulness and scale remain unmeasured.

## Remaining limits and delivery

Independent reviewers/viewers available today: none. Owner review is editorial evidence only. No new paid model calls were made for this category presentation. The corner panel is deterministic; the guide has no corner-specific action. The new video is uploaded privately for owner review and must be approved, made public and checked signed out before submission. No additional Foundry services, infrastructure, productivity result or uptime guarantee is claimed.
