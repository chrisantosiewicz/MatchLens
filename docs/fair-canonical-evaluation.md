# Fair canonical comparison — October 22

This replaces the earlier free-text-vs-canonical comparison as the relevant engineering comparison. It does **not** establish a semantic-quality winner or viewer benefit.

## Frozen scope and actual execution

`docs/frozen-fair-canonical-v1.json` hashes 22 core/evaluator source files, including the final checker contract. The final core files still match those hashes. Six fresh eligible passing cases span seeds 5201, 5209 and 5227, three player IDs and both teams. Four have two eligible choices and two have one. Cases were selected for nonempty candidate coverage before model execution, not sampled as a representative football population. Four boundary cases are reported separately.

All policies receive the same canonical candidate/claim ledger. Fixed editorial ranking selects the first server-ordered eligible candidate. The one-call selector and three-role chain can select those same sentences or fall back; neither can write new factual prose. The model/deployment, synthetic facts, selected clocks and canonical rendering are shared. Evaluation order was fixed and each eligible policy/case was run once, so latency, caching and model sampling are not controlled performance estimates.

Policy | Eligible cases exercised by model | Canonical model selections | Fallbacks | Calls | Median exercised case | Input / output tokens
---|---:|---:|---:|---:|---:|---:
Deterministic | 0 | 0 | 0 | 0 | — | 0 / 0
One canonical selector | 6 | 4 | 2 | 6 | 1,562.72 ms | 33,459 / 479
Three roles | 6 | 3 | 3 | 16 | 4,954.07 ms | 86,124 / 1,400

Every policy also handled four deterministic boundaries without model calls. Those are not counted as model-exercised cases. Fallbacks provide local answers but do not count as successful model selection. Unknown/unapproved IDs and a checker veto were retained. Usage is measured tokens, not measured dollar cost. The overall run made 34 calls including checker probes, below the hard cap of 36; no hidden retries were requested.

In 5201-north-6 the fixed ranking selected a recent progressive-pass sequence ending in a teammate turnover; both model policies selected an earlier shot build-up. This is an observable editorial choice. It requires independent football review to establish whether it is more useful. In other cases identical text or fallback predominated. Do not infer an advantage merely from different text or a model selecting a valid ID.

## Checker challenges

The isolated checker was given 12 developer-authored probes: eight flawed proposals across wrong scope, irrelevant-but-factual content, overgeneralization and omitted limitations, plus four supported controls. Some controls/proposals are repeated variants; this is not 12 independent football situations. These deliberately corrupted proposals are **not** eligible production claims.

- Two overgeneralizations were vetoed.
- Five flawed proposals were accepted.
- One flawed proposal produced incomplete checks and was blocked by the contract; it is unresolved as a model editorial decision.
- All four supported controls were accepted.

This shows limited sensitivity and real false acceptance. It does not justify treating the checker as a reliable semantic verifier. The server's typed facts, scope validation, canonical sentences and publication gates remain essential. A veto on an injected proposal does not demonstrate incremental production errors prevented, because the production ledger already excludes those proposals.

## Product decision

Do not make three agents the preferred workflow or pursue an agent-count claim. Keep the useful local default. Offer `MATCHLENS_AI_POLICY=canonical_single` for controlled Foundry selection; retain `evidence_chain` as an experimental comparator. The one-call policy is the lower-call option, with no proven quality sacrifice in this unreviewed sample; that is not proof of semantic equality. Anonymous public operation remains template mode. The recorded execution is available in the functioning review page so judges need not configure Azure to inspect it.

## Human evidence and reproduction

Independent review fields remain null. Actual viewer-study participants: **zero**. The phone-ready study and label-blinded report review are prepared; developer QA is excluded from participant results. See [human-review protocol](human-review-protocol.md). No willingness-to-pay, market-demand, comprehension-gain, reliability or superiority claim is made.

```powershell
backend/.venv/Scripts/python.exe scripts/evaluate_canonical.py --manifest docs/frozen-fair-canonical-v1.json --output artifacts/new-fair-run.json --live
backend/.venv/Scripts/python.exe scripts/summarize_canonical.py docs/evaluations/fair-canonical-v1.json artifacts/recomputed-summary.json
backend/.venv/Scripts/python.exe scripts/build_review_package.py --results docs/evaluations/fair-canonical-v1.json --summary docs/evaluations/fair-canonical-summary-v1.json
```

The live command requires authenticated Foundry mode and makes bounded billable requests. It refuses changed frozen source and existing output. No new calls are needed to reproduce the summary or public recorded pages. Source facts, raw handoffs, usage, failures and null human fields remain in `docs/evaluations/fair-canonical-v1.json`; concise descriptive results are in `fair-canonical-summary-v1.json`.

Final verification: 114 backend tests and 24 frontend tests pass; lint, JavaScript syntax check and production build pass. Browser QA verified required-answer validation, advancement, label-hidden report ratings, the same-metric contrast and actual correction recomputation. QA sessions were marked as development involvement and are not participant evidence.
