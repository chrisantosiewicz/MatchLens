# Current AI workflow

See [STATUS.md](../STATUS.md) for current acceptance. Default local and public operation uses deterministic templates. The optional `single` policy invokes Foundry for supported English why/change interpretation only; direct counts, Spanish and unsupported tracking/causal requests stay deterministic. The shared routing helper is used by application and evaluation.

The deterministic packet supplies viewer clock, window bounds/durations, player active minutes, player contributions/rates, team entry rates, structured facts, event IDs and uncertainty. The model must preserve the calculated rate direction. Structural validation rejects unknown IDs/numbers/rate contracts, including unsupported signed values; ordinary minute ranges are parsed separately from negatives. Matching values and IDs still do not establish semantic support.

Foundry uses the declared/locked Azure AI Projects2.0.0 OpenAI-compatible Responses client and Entra authentication. Clients close deterministically; credential tokens stay in process memory. Transport timeout8seconds/retries0/output cap600tokens are not an end-to-end SLA. Process-local default budgets6requests/minute and50/session are not a dollar ceiling or public authentication. Public hosting has no paid model calls enabled.

The specialist comparator selects canonical sentences through Analyst/Reviewer/Producer application code; it is not Agent Framework integration and has shown no reliable relevance/quality advantage. Fewer single-model calls did not mean lower estimated cost: its context was larger. Routing differences prevent isolating orchestration effects.

Evidence: evaluation-results.json (initial raw policy), evaluation-current-results.json (d814db3 hybrid contract), foundry-current-verification.json (fresh505/606 developer review), deployment-model-verification.json (actual deployment SKU/version). None establishes final independent semantic acceptance. English-only routing added October22 invalidates any claim that earlier bilingual experiments measure the current exact policy.

## October22 frozen narrow workflow

Current trace: evaluations/frozen-v4.json; manifest frozen-english-v4.json; backend source6da84d6. Twelve paired cases, four actual model calls. Sparse/no-active-baseline/zero-duration/no-passing inputs return deterministic limitations before provider creation or quota consumption. Concept guards are conservative heuristics, not semantic proof.

Accepted results retain model_cited_event_ids separately from evidence_ids, which unions model citations with complete deterministic metric sources. fact_support provides each count, duration, rate, exact source IDs and window bounds; metric_definition explains progression without implying quality. The recorded evidence viewer renders these separately. Historical v1 failures remain; replay_recorded_failure.py feeds an actual saved bad response through the current guard without remote generation. See evaluations/v4-ai-review.md and independent-review.md for limits and external acceptance.
