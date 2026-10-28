# MatchLens submission copy — October 27

For the final recommended copy, exact links and bounded owner decisions, use [FINAL-REVIEW.md](FINAL-REVIEW.md). It replaces the earlier open-ended review workflow.

Owner review and final submission are pending. Recommended category: **Best Use of Microsoft Foundry**; owner choice is unconfirmed.

## Short registration pitch

MatchLens helps football viewers explore the actions behind a match moment. Deterministic statistics and event-linked explanations follow the selected replay clock; an optional Microsoft Foundry analyst and viewing guide support interpretation and exploration. The local demo uses visibly synthetic matches and keeps useful template answers available without cloud access.

## Judge description

A lateral pass can disappear inside a pass total. MatchLens lets a viewer inspect Mateo Silva's 69:07 pass and the recorded sequence that ends with Nico Vega's saved attempt at 69:22. The [recorded sequence](owner-editorial-review-2026-10-25.md) links `match-7-shift-e710` revision 1 to the attempt at `e713`. It establishes participation in that sequence; it does not establish that Silva created space or caused the attempt.

The local corner scenario adds complete, explicitly synthetic position snapshots. Viewers can compare two attackers in the box at setup with five at delivery, inspect the eight defending players at delivery, and follow recorded first contact and outcome. English and Spanish answers and recaps respect the selected clock. Unsupported tactical conclusions are withheld, and corrected source events invalidate dependent output. [Corner implementation and local evidence](corner-context.md) document these boundaries.

Statistics, claim eligibility and evidence IDs come from deterministic server logic. The optional Foundry analyst selects supported interpretation; a separate viewing guide ranks available server-authored next actions. Recorded authenticated execution is inspectable alongside local results and retained failures. Template, recorded model and fallback outputs have distinct labels.

## Azure contribution

Microsoft Foundry supplied actual authenticated `gpt-4.1-mini` analyst and guide execution through a backend Azure AI Projects/OpenAI-compatible integration with Azure identity. The recorded guide trial contains eight model calls: one analyst and seven guide calls; all seven guide outputs passed catalog-selection validation. This establishes operational execution, not improved understanding or reliable football interpretation. The browser contains no model credentials and the public demo makes no paid model calls.

An older template build was verified on Azure App Service's free tier. The latest corner extension runs locally; Azure redeployment is on hold at the owner's request. No new infrastructure, live sports feed, video recognition or real tracking is claimed.

## Limits and links to supply

All match data and position frames are synthetic. Sparse snapshots support occupancy and endpoint movement only, without intended targets, continuous trajectories or defensive reactions. Event coordinates alone do not establish off-ball behavior or causation. Seed checks are heuristic sanity checks, not empirical calibration. Independent human evaluations total zero; owner editorial feedback and valid model selections do not establish viewer benefit. Earlier free-text model failures are retained in the evidence.

- Source: [MatchLens public repository](https://github.com/chrisantosiewicz/MatchLens); confirm final delivered revision.
- Existing public demo: [October 22 template guide build](https://matchlens-chris-demo-2026.azurewebsites.net); recheck access and identify its older version.
- Latest local build: final reviewed source/test-build package and [English setup](judge-guide.md).
- Video: [replacement private owner review](https://youtu.be/9Jr04kSZD5w), uploaded and saved Private with owner playback started. Public publication and anonymous playback verification remain pending owner approval. It is an edited browser UI capture with narration, not continuous native screen recording.

Keep private organizer keys and credentials out of submission copy and all public artifacts. Owner must confirm rights, eligibility, license, category and final submission receipt separately.
