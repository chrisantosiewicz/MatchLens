# Current AI workflow

See [STATUS.md](../STATUS.md) for current acceptance. Default local and public operation uses deterministic templates. The optional `single` policy invokes Foundry for supported English why/change interpretation only; direct counts, Spanish and unsupported tracking/causal requests stay deterministic. The shared routing helper is used by application and evaluation.

The deterministic packet supplies viewer clock, window bounds/durations, player active minutes, player contributions/rates, team entry rates, structured facts, event IDs and uncertainty. The model must preserve the calculated rate direction. Structural validation rejects unknown IDs/numbers/rate contracts, including unsupported signed values; ordinary minute ranges are parsed separately from negatives. Matching values and IDs still do not establish semantic support.

Foundry uses the declared/locked Azure AI Projects2.0.0 OpenAI-compatible Responses client and Entra authentication. Clients close deterministically; credential tokens stay in process memory. Transport timeout8seconds/retries0/output cap600tokens are not an end-to-end SLA. Process-local default budgets6requests/minute and50/session are not a dollar ceiling or public authentication. Public hosting has no paid model calls enabled.

The specialist comparator selects canonical sentences through Analyst/Reviewer/Producer application code; it is not Agent Framework integration and has shown no reliable relevance/quality advantage. Fewer single-model calls did not mean lower estimated cost: its context was larger. Routing differences prevent isolating orchestration effects.

Evidence: evaluation-results.json (initial raw policy), evaluation-current-results.json (d814db3 hybrid contract), foundry-current-verification.json (fresh505/606 developer review), deployment-model-verification.json (actual deployment SKU/version). None establishes final independent semantic acceptance. English-only routing added October22 invalidates any claim that earlier bilingual experiments measure the current exact policy.

## October22 frozen narrow workflow

Current trace: evaluations/frozen-v4.json; manifest frozen-english-v4.json; backend source6da84d6. Twelve paired cases, four actual model calls. Sparse/no-active-baseline/zero-duration/no-passing inputs return deterministic limitations before provider creation or quota consumption. Concept guards are conservative heuristics, not semantic proof.

Accepted results retain model_cited_event_ids separately from evidence_ids, which unions model citations with complete deterministic metric sources. fact_support provides each count, duration, rate, exact source IDs and window bounds; metric_definition explains progression without implying quality. The recorded evidence viewer renders these separately. Historical v1 failures remain; replay_recorded_failure.py feeds an actual saved bad response through the current guard without remote generation. See evaluations/v4-ai-review.md and independent-review.md for limits and external acceptance.

## Meaning-led workflow (supersedes rate-only prompt)

sequence_stories supplies verified story cards: recorded same-team involvement before a teammate shot; progressive pass followed by an observed turnover without an intervening shot; selected-player turnover followed by an opposition shot within20seconds without observed own regained possession. Examples are bounded to the comparison window. Build-up uses30seconds. These are editorial heuristics, not assist/causal or decision-quality models.

The model receives model_context's curated rates and story metadata, not raw coordinates or all-action totals. It explains contribution, selects story IDs and cites every event in each selected story. Backend checks source/clock/number/rate contracts; full deterministic sources are retained separately. Template/fallback answers retain their own story sources and render narratives without model access. Spanish remains deterministic, including translated outcome labels.

V7:8paired cases,4requests,1accepted experimental explanation,1guard fallback,2timeouts. Failed trials v5/v6 remain; they are not quality successes. Independent review remains pending. View exact reconstructed input (not an independently captured request) and all outputs at /evidence/index.html. Actual measured transport times are not an8second end-to-end guarantee.

## Location/editorial update (current)

editorial.py supplies policy_version, source revision, coverage, exposure, matched player/team entry comparisons and eligible story facts. model_context removes ineligible conclusions. stories expose geometric action origin/destination/distance, pass rank within last3completed passes, exact loss actor and intervening actions, recovery outcome and time/action caps. Raw pitch coordinates remain outside model input. Fan/analyst use the same conclusions and sources.

V8 uncovered subject/metric/exposure errors despite structural acceptance. V9 still raised semantic concerns. Current conservative regression guards reject the saved v9 candidates in a separate offline replay; this is not new model generation or a quality benchmark. The main recorded viewer shows guarded local results with original model prose separately inspectable. Raw freezes remain immutable and match generation source, not later guard changes. No claim of current independent semantic acceptance. Local deterministic location explanations remain useful.

Regenerate the current recorded viewer in order from frozen generation source: build_recorded_evidence.py(v9), then replay_location_candidates.py from current guard source. The first step refuses changed source; use the recorded generation revision for that step. The already exported review files remain runnable without regeneration. New live evaluation requires a new manifest with current source hashes/cases, not modification of old traces.
