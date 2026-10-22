# Frozen capability review

Scope: English duration-aware player/team interpretation with deterministic Spanish. Manifest: frozen-english-v4.json. Cases/seeds and normalized source hashes were fixed before any live call for this candidate. Do not tune against outputs and call the same cases held out; version the candidate and reserve new cases after changes.

Offline validation (no model claims):
```
backend/.venv/Scripts/python.exe scripts/run_frozen_evaluation.py --manifest docs/frozen-english-v4.json --output artifacts/frozen-offline.json
```
Live (requires configured authenticated Foundry; billable, at most4 model requests under current input boundaries):
```
backend/.venv/Scripts/python.exe scripts/run_frozen_evaluation.py --manifest docs/frozen-english-v4.json --live --output artifacts/frozen-live.json
```
The runner rejects changed source and existing output paths. It records canonical facts, window durations, source IDs, provider calls/usage, diagnostics and latency. Missing calls are skips, not zero-cost model successes. human_review remains null. The manifest is a freeze declaration, not evidence of a run or acceptance.

A person other than the developer must review each output against its context. Record reviewer identity/role and date, then pass/fail/uncertain plus notes for: correct subject, correct time/window, every factual statement supported by the facts and cited events, relevance, appropriate abstention, and honest uncertainty. Valid IDs alone do not establish support. Distinguish all actions from passes and descriptive rate changes from effectiveness/causation. Sparse observations cannot establish absence of real activity. Check fallback and unsupported questions separately from model refusals.

Review blind to policy if possible; record any unblinding and disagreements. Provisional gates: no unsupported published factual claims in reviewed sample, >=90% relevant supported requests, >=95% appropriate unsupported-request refusals. Report denominators and failures. Small samples do not establish population reliability. Actual v4 live run: evaluations/frozen-v4.json, source6da84d6. Developer/second-AI review: evaluations/v4-ai-review.md. Independent human acceptance is pending. Current backend normalized hashes must match; later frontend/docs commits do not change that freeze.

## Current meaning-led candidate

Use frozen-meaning-v7.json and evaluations/frozen-meaning-v7.json for the current richer flow. The earlier commands and v4 report above describe the historical rate-only candidate; do not rerun them against changed backend source. To reproduce v7, pass --manifest docs/frozen-meaning-v7.json explicitly. Judge support, relevance, sequence attribution, time-window clarity and appropriate uncertainty, including fallback. Four attempted live requests produced one accepted output, one rejection and two timeouts. All eight cases remain visible. No independent human acceptance exists. See football-meaning-review.md for owner editorial questions, distinct from evidence verification.
