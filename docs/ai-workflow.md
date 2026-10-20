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
