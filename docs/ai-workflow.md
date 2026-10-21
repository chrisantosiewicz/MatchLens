# AI workflow readiness

Default operation is deterministic template mode. No Azure subscription, Foundry project, deployed model, or service access has been verified. Do not claim live AI integration.

`workflow.py` defines a provider-independent bounded state machine:

1. Analyst chooses one named tool from a request-scoped allowlist.
2. Tool executes deterministic statistics against the selected player and viewer clock.
3. Reviewer accepts, requests revision, or abstains.
4. At most two analytical attempts are allowed; this implementation uses at most two tool calls (below the eight-call ceiling).
5. Producer selects and orders supplied fact IDs.
6. Validator permits only canonical factual sentences and known evidence IDs. Extra prose or invalid IDs trigger fallback.

This deliberately conservative implementation prevents free-form numerical invention at the composition boundary. It does not prove every possible interpretation or establish that three agents outperform one.

The optional `FoundryProvider` uses the Projects client's OpenAI-compatible Responses API with Entra authentication and bounded request timeout/retries. Cloud smoke testing, SDK version pinning and measured latency are deferred until account setup. The currently installed skill examples and current SDK docs differ across versions; use the documented selected version rather than mixing examples. Agent Framework SDK integration is not yet implemented; current orchestration is application code.

Reference inspected October 20, 2026:
https://learn.microsoft.com/en-us/python/api/overview/azure/ai-projects-readme?view=azure-python-preview

Required next evaluation: single-agent baseline versus specialist workflow using identical tools, held-out questions, unsupported-causation/tracking requests, translation pairs, timeout cases and latency/token usage. Scripted tests prove orchestration logic, not model quality. Bilingual and user research have not occurred.


## October 21 candidate (not live-verified)

`MATCHLENS_AI_POLICY=single` invokes `explainer.py`: one model request receives a clock-limited structured packet with selected-player totals, contributions before/after the anchor, team comparison, actual durations, event records/IDs and uncertainty. It can generate new interpretive prose rather than select a template. Structural validation checks output length, source-ID membership and numeric-token membership. These checks cannot prove semantic support or relevance; publication quality must be evaluated manually. The UI labels model output for inspection rather than calling all model claims verified.

Foundry SDK `azure-ai-projects==2.0.0`, identity and OpenAI dependencies are declared in the optional extra and resolved in uv.lock. Installation alone is not cloud verification. Provider client reuse, process-wide time budgets and public model access limits remain unfinished. Single-call timeout limits request transport work, not a guaranteed end-to-end service latency.

Official SDK reference checked October 21: https://learn.microsoft.com/en-us/python/api/overview/azure/ai-projects-readme . A real authenticated smoke test remains required.


October 21 live verification update: tenant-specific authentication succeeded against the supplied Foundry project. Two gpt-4.1-mini Responses calls returned model output and token usage. Neither candidate passed structural output validation; the first introduced unsupported numeric tokens (89 and 100). Fallback remained active. See `docs/foundry-verification.json` (or `foundry-verification.json` from this directory). Earlier statements of no live requests are historical; a passing interpretation, semantic quality and reliability remain unverified. Next: retain rejected candidate diagnostics, repair output-contract adherence, then paired live evaluation. Do not widen validators merely to obtain a passing demo.


Current contract update: exact decimal equivalence accepts 100 and 100.0; incidental event-ID/coordinate digits do not authorize narrative numbers. Provider requests strict JSON schema for interpretations and records usage/status/latency per call. Evaluation sessions reuse the transport; credentials are shared in process memory and closed on process exit. API request providers close transports in finally blocks. Rejected candidate diagnostics stay in local evaluation artifacts, not public answer bodies. Explicit team/player subject guides and human-readable anchor/window bounds are supplied. None of these checks proves semantic support. See evaluation.md for observed failures and routing changes.
