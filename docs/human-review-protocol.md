# Human evaluation: ready, no results yet

## Shareable pages

- Viewer comparison: `/review/?mode=study` (5–8 minutes).
- Independent report review: `/review/?mode=blind` (12–18 minutes).
- Football demonstrations: `/review/`.
- Actual recorded Foundry selection, alternatives and failures: `/review/?mode=execution`.

The public pages make no paid model calls and require no accounts. Answers remain in page memory. Participants download a JSON file and decide whether to send it to the organizer. Do not refresh before downloading. No messages or invitations have been sent by the agent. No human responses have been created or counted.

## Recruit and review

Invite viewers directly through `/review/?mode=study`, before they view the demonstrations or reports. Prior exposure is asked explicitly and same-page demo/report exposure is tracked conservatively. Exposed or unsure sessions are excluded from the first-use comprehension summary. Ask 4–6 willing football viewers, including casual and knowledgeable viewers, to complete the viewer comparison without external tools. Ask at least one football-knowledgeable person uninvolved in development to complete the separate report review. Do not describe a preferred policy or tell participants which answer should win. Record recruitment method and actual completions; do not call this market validation.

Sample invitation to send yourself: “Could you try this short fictional-football comparison on your phone? We’re checking whether explanations help people interpret the same event facts. No account or personal details are needed. At the end you can download an anonymous answer file and send it back if you choose. There are no right opinions about which format you prefer.”

Review labels are shuffled and hidden in the interface, including checker badges. Some reports are identical; some are local fallbacks. All reports receive the same full-clock selected-player statistics, definitions, candidate facts, window calculations and event sources. Review support, relevance, subject/time scope, limitations, missing qualifications and usefulness separately. The organizer key in ignored local `artifacts/review-unblinding.json` is for the organizer after submissions. This is interface-label blinding, not secure or double blinding; reviewers should avoid inspecting the repository beforehand. Their independence is self-reported, not independently verified.

## Viewer comparison design

Six synthetic situations cover hidden involvement, opposite player/team entry rates, and incomplete coverage. For each pair, one situation is assigned statistics plus event log and one is assigned the same facts plus a MatchLens explanation. Assignment and trial order are randomized within each session. Every participant sees three situations per format; no exact situation repeats within that session. The two versions share all factual inputs. Paired variants share underlying synthetic structures, so do not treat trials as independent match samples.

Each situation asks two factual/interpretive multiple-choice questions, confidence (1–5), and whether the viewer was interrupted. Measure accuracy, trial time and confidence separately. Time is reading plus answering, not a pure answer-search benchmark. Interrupted trials remain in accuracy results but are excluded from time summaries. A small convenience pilot cannot establish demand, willingness to pay, significance or general reliability.

## Process real exports

```powershell
backend/.venv/Scripts/python.exe scripts/score_viewer_study.py --responses <actual-export-files> --output artifacts/viewer-pilot-results.json
```

Developer/QA, incomplete and previously exposed/unknown-exposure sessions are excluded from the primary first-use analysis. Exposure remains self-reported across reloads or other devices; this is not a verified blinded first-exposure trial. The script refuses duplicate participant codes and incomplete/unbalanced trial sets. With no real exports it reports `awaiting_real_participants` and null outcome metrics. Never commit participant notes or raw exports without their permission. For independent report review, match anonymous option IDs to the organizer key only after ratings are complete; keep uncertain answers rather than treating them as failures or approvals.

## What remains unfinished

Actual independent report ratings and actual viewer responses are required before claiming semantic quality or viewer benefit. The demonstration video remains unfinished and deferred. A suggested sub-two-minute sequence is hidden contribution first, then player/sequence inspection, misleading attribution or correction withdrawal, then language adaptation and the actual recorded Foundry handoff. Use functioning software and label scripted examples, local explanation and recorded model execution accurately.

The organizer key is excluded from Git, public hosting and the judge ZIP. Regenerating the package writes it only into ignored local artifacts. Automatic approval review prevented an attempted public commit containing that key; it was removed before any public push.
