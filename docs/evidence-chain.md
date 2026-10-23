# Evidence analysis → conclusion → checker

This opt-in recommendation workflow uses three separate Foundry prompts over one deterministic ledger. It is not Microsoft Agent Framework integration, and using the same underlying model does not provide independent verification.

1. **Evidence analysis** selects eligible sequence candidates and optional qualifying counter-evidence. It receives calculated context, window durations, player contributions, editorial gates and claim cards.
2. **Conclusion** chooses one approved interpretation. It cannot replace player names, metrics, numbers or wording with invented prose.
3. **Checker** reviews every proposed observation, interpretation and limitation. Missing checks, unknown IDs, stale snapshots, unsupported verdicts or a veto preserve the local answer.

The server publishes canonical sentences tied to typed facts and editorial rules. This is model-directed interpretation selection, not unrestricted model-written explanation. Passing candidates must begin with the selected player's pass. Before/after comparison questions remain local until a typed comparison-claim contract is implemented; a sequence alone is not a comparison. English interpretive questions are eligible; Spanish remains a practical deterministic demonstration using the same factual rules.

## Evidence trail

Each canonical sentence exposes its subject, time scope, fact IDs, rule version, supporting event IDs and revisions. A request snapshot binds the selected clock, source revision, player, question, language and editorial policy. The API rechecks the source after the three calls and refreshes locally if a correction arrived. The primary sequence is separated from aggregate-stat sources; valid IDs alone do not prove meaning or causation. Legacy free-text model outputs do not inherit canonical template sentence badges.

The player panel provides **Sentence-by-sentence evidence**, model-stage statuses, exact fact values and source revisions. `not_run` means no model checked the claim. Counts and other outputs without canonical sentence coverage do not receive sentence-level claim badges. Aggregate sources remain separately inspectable. The audit UI is chiefly technical English; the football narrative supports English and Spanish.

## Run and verify

Default mode remains local and default policy remains `single`. To exercise this workflow, set `MATCHLENS_AI_POLICY=evidence_chain` server-side. With `MATCHLENS_AI_MODE=template`, all agent stages are explicitly `not_run` and there are zero model calls. With configured authenticated Foundry mode, each eligible answer makes at most three sequential calls. Every actual role call consumes the existing process request budget. No browser credentials are required or exposed. Public hosting keeps paid model calls disabled.

```powershell
backend/.venv/Scripts/python.exe -m pytest backend/tests -q
backend/.venv/Scripts/python.exe -m ruff check backend scripts/run_frozen_evaluation.py
cd frontend
npm test
npm run build
```

For a frozen paired evaluation, use `scripts/run_frozen_evaluation.py --manifest <manifest> --output <new-file> --include-chain --live` from an authenticated environment. This makes billable requests. Source hashes must match and existing results cannot be overwritten. Without `--live`, model-needed rows are skipped. Recorded usage is tokens, not measured dollar cost. Independent human semantic review remains required.

## Recorded limitations

The first bounded live run, `docs/evaluations/evidence-chain-v1.json`, includes a passing question wrongly answered with a recovery sequence despite checker acceptance. It is retained as failed relevance evidence. The revised candidate adds a deterministic topical gate and keeps comparison questions local. Do not cite the first run's checker acceptance as semantic success. The small paired smoke runs are not evidence of superiority over templates or a single model, nor a reliability/latency guarantee. Counter-evidence is limited to supplied eligible event sequences; it is not a complete tactical assessment. No tracking, video recognition, defensive line, intent or causal claims are introduced.

Revised live smoke (`docs/evaluations/evidence-chain-v2.json`): one English passing explanation completed all three roles in 5606.01 ms, using 19616 input and 309 output tokens. It selected a third-last pass before a saved shot, with exact sequence sources and a non-causal limitation. The comparison question remained local; causal/tracking requests and Spanish used zero model calls. The same passing question's single-model comparator completed in 2234.84 ms; this tiny sample does not establish a quality advantage and the three-role path cost more tokens/calls. Human review fields remain null.

Final local verification: 100 backend tests, 24 frontend tests, backend lint and production frontend build pass. Final checker hardening also rejects contradictory supported/irrelevant verdicts; that tightening is covered locally and was added after the v2 live freeze. The v2 live results therefore describe its recorded source hashes, not the final patched source.
