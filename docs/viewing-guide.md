# Match analyst and viewing guide

Approved direction: retain the one-call evidence-grounded match analyst, and give the second role the distinct job of helping viewers decide what to explore. This is a bounded extension of the existing question/suggestion flow, not another verification chain. Product-specific agent instructions belong here and in the provider prompt; no new reusable Codex skill is needed.

## Guide capabilities

- Clarify broad questions such as “Is he playing well?” through explicit topic choices; do not infer what “well” means.
- Select up to three available next actions from a deterministic server catalog.
- Explain a concept at fan or analyst depth, in English or Spanish.
- Open exact recorded sequences and comparable player/team box-entry windows.
- Explain unavailable evidence and uncertainty; never recommend a tool the feed cannot support.

The guide cannot write new match claims, invent a tool, change the clock, infer preferences beyond explicit branch/depth choices and clicks, or declare another agent's answer verified. Optional model use ranks action IDs with one bounded call; all visible labels/content/actions are server-authored. Local ranking remains useful when the model is disabled, unavailable, malformed or over budget. Analyst answers render independently of guide requests.

## Knowledge branches

Branch | Explore | Evidence boundary
---|---|---
Attacking | Progression, recorded shot build-up, box access, shots and transitions after a recovery | No invented chance quality, defensive line breaks, assists or causation
Defending | Recorded recoveries/tackles, turnover-to-opposition-attempt sequences, the limits of defensive event counts | No inferred pressure, marking, block shape, nearby support or sole blame
Neutral | Circulation, backward/lateral passes, resets, comparable involvement and definitions | No possession-time percentage, tempo-management intent or quality inferred from completion alone

Transitions can link attacking and defending. These are viewer-selected knowledge branches, **not** an automatic match-phase classifier. “Neutral” is this product's navigation category for circulation and general context, not a synonym for FIFA's “in contest.” Build-up can contribute to attacking play. The reference vocabulary distinguishes possession, progression and defensive phases: [FIFA Training Centre, in possession](https://www.fifatrainingcentre.com/en/resources-tools/football-language/in-possession/index.php) and [FIFA Enhanced Football Intelligence definitions](https://www.fifatrainingcentre.com/media/native/world-cup-2022/Enhanced%20Football%20Intelligence%20EN.pdf). These references do not validate tactical inference from MatchLens event data.

## Interaction and grounding

The player panel offers Attacking / Defending / Neutral and an explicit request for guidance. A broad question returns local clarification, not a model performance verdict. After an answer, the viewer can request next steps; there is no mandatory second model call. Clicking a concept, sequence or comparison opens existing facts locally; an ask action goes through the analyst endpoint.

Every response carries player, selected clock, source revision and a catalog snapshot. Sequence and metric actions carry exact event IDs/revisions. Definitions are explicitly knowledge content, not match evidence. Unknown action IDs, duplicate selections, additional prose, snapshot mismatch and changed source are rejected. Corrections invalidate pending guidance. Guidance stays explicitly pinned to its displayed answer/request clock during forward playback, with an Update to current clock action. A follow-up question uses that same pinned clock. Rewinding clears guidance and pending responses. Explicitly explored actions are omitted from later suggestions within that player context.

## Delivery and acceptance

1. Add branch registry, deterministic eligibility/catalog, one-call guide selection and safe fallback. Test availability, branches, multilingual labels, duplicates/unknown IDs, clock/source bounds, local zero calls and budgets.
2. Add local broad-question clarification and event-grounded defensive answers. Preserve analyst evidence and avoid attack-only answers to defensive questions.
3. Add an independently loaded guide component; test answer-first rendering, exploration actions and invalidation on clock/language/source/player changes.
4. Run fresh bounded recorded guide selection against the same local catalog; record source hashes, role inputs/outputs, usage, latency and failures. This demonstrates operation, not viewer benefit.
5. Verify the public template experience and publish updated evidence/docs. Human comparison remains needed: analyst plus fixed suggestions versus analyst plus guide, measuring relevant next steps, comprehension, time and unnecessary clarification. Keep the simpler option unless additional value is observed.

Public paid model calls remain disabled. No preference database, extra orchestration framework, tracking, video recognition or new cloud infrastructure is introduced.

## Verified implementation — October 22

Implemented `/guidance`, strict optional Foundry action selection, on-demand player-panel navigation, local fallback, English/Spanish concepts and defensive answers. Sequence IDs now follow story identity across branches, with filtering before the two-sequence limit. Regression tests reproduce and fix cross-branch suppression and guide clearing during replay before a future comparison anchor. A read-only implementation review identified those two defects; both fixes passed the reproductions.

Fresh verification: 124 backend tests, 30 frontend tests, Ruff and production build passed. Browser checks covered the independent answer, attacking concept/reference, defensive counts, Spanish follow-up and language reset. A browser-discovered aggregate-source display bug was reproduced and fixed: a count answer without sequence claims now exposes its aggregate event IDs. Tests also cover stale sources, corrections during generation, incomplete coverage, invalid selections, budgets and rewind.

`frozen-viewing-guide-v1.json` freezes the evaluated backend, frontend integration and runners. `evaluations/viewing-guide-v1.json` records eight real Foundry calls: one canonical analyst selection followed by one guide selection, plus six other guide selections. Seven of seven guide calls returned valid catalog selections; the broad clarification case made no call. Guide median latency was 1,355.72 ms. Total trial usage including the analyst was 22,924 input and 431 output tokens. These are operational observations from developer-selected cases, not semantic acceptance or reliability rates. No monetary cost is estimated without the account's actual billing rate.

The model sometimes reordered the local suggestions and sometimes selected the same ones. That establishes neither better guidance nor greater understanding. Independent human relevance review and a comparison of fixed suggestions against guide suggestions remain pending. Historical fair-canonical source hashes describe their earlier freeze and do not verify this newer implementation. The recorded guide trial also precedes the final aggregate-source display fix in `PlayerPanel.tsx`; backend, provider prompts and trial runner are unchanged. `frozen-viewing-guide-final.json` freezes the final source and has a fresh zero-call local run. No new paid model run is claimed for that UI-only fix.

Reproduce in PowerShell (authenticated Foundry mode needed only for `--live`; default trial is local):

```powershell
backend/.venv/Scripts/python.exe scripts/evaluate_guide.py run --manifest docs/frozen-viewing-guide-final.json --output artifacts/my-guide-local.json
backend/.venv/Scripts/python.exe scripts/evaluate_guide.py run --manifest docs/frozen-viewing-guide-final.json --output artifacts/my-guide-live.json --live
backend/.venv/Scripts/python.exe scripts/build_guide_evidence.py
```

The runner refuses changed frozen source or an existing output. Do not overwrite recorded runs to hide failures. The evidence page explicitly presents recorded execution; the public application remains local/template.

## Knowledge sourcing and plugins

The available plugin catalog search did not return a suitable football knowledge integration. No football plugin was installed. Use a small attributed reference library instead: FIFA Training Centre's in/out-of-possession vocabulary and England Football Learning's game-phase explanation (links above and on concept cards). Definitions are original short summaries; the progressive-pass threshold is explicitly MatchLens's own metric. These sources are background concepts, never substitute match evidence. IFAB is the primary reference for future laws explanations, not presently a match-reasoning dependency. A live football-data API is a separate data supplier, not proof of tactical knowledge, and is outside this synthetic-only prototype.
