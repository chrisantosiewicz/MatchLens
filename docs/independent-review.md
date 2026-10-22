# Frozen capability review

Scope: English duration-aware player/team interpretation with deterministic Spanish. Manifest: frozen-english-candidate.json. Cases/seeds and normalized source hashes were fixed before any live call for this candidate. Do not tune against outputs and call the same cases held out; version the candidate and reserve new cases after changes.

Offline validation (no model claims):
```
backend/.venv/Scripts/python.exe scripts/run_frozen_evaluation.py --output artifacts/frozen-offline.json
```
Live (requires configured authenticated Foundry; billable, at most9 interpretation requests):
```
backend/.venv/Scripts/python.exe scripts/run_frozen_evaluation.py --live --output artifacts/frozen-live.json
```
The runner rejects changed source and existing output paths. It records canonical facts, window durations, source IDs, provider calls/usage, diagnostics and latency. Missing calls are skips, not zero-cost model successes. human_review remains null. The manifest is a freeze declaration, not evidence of a run or acceptance.

A person other than the developer must review each output against its context. Record reviewer identity/role and date, then pass/fail/uncertain plus notes for: correct subject, correct time/window, every factual statement supported by the facts and cited events, relevance, appropriate abstention, and honest uncertainty. Valid IDs alone do not establish support. Distinguish all actions from passes and descriptive rate changes from effectiveness/causation. Sparse observations cannot establish absence of real activity. Check fallback and unsupported questions separately from model refusals.

Review blind to policy if possible; record any unblinding and disagreements. Provisional gates: no unsupported published factual claims in reviewed sample, >=90% relevant supported requests, >=95% appropriate unsupported-request refusals. Report denominators and failures. Small samples do not establish population reliability. No independent review or live run has been claimed for this candidate.
