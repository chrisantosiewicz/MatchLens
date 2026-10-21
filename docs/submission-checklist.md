# Submission recovery checklist — October 21

This supersedes the infrastructure-heavy portions of the original plan. Local fixes are authorized for inline execution. Deadline target: October 27; final rules and registration status must be verified before submission.

## Review triage against current source

Confirmed: sparse one-team sampling; excessive pass completion; goalkeeper season shots; wrong-tool timeout fallback; zero-duration comparison; hard-coded health status; undeclared Foundry SDK; replay rather than live ingestion; store disconnected from serving; canonical sentence selection rather than rich interpretation; no production routing/package; no public remote or video supplied. Five-entry threshold is an editorial gate, not statistical significance. Existing clock safeguards and percentile arithmetic are supported by tests, not proof of broad accuracy.

Packaging clarification: `.env.example` exists locally but was deliberately excluded from the judge ZIP. Restore a sanitized configuration example in future handoffs. Screenshot is an illustrative scene, not video recognition. No reviewed defect was already resolved when this checklist was created.

## Ordered milestones

1. [x] Data validity (local): balanced missing-observation sampling from complete ground truth; role-sensitive completion and season distributions; failed passes end possession. Validate seeds 0–19 for completion bounds, both teams, valid active players, goalkeeper shot limits. Regenerate committed fixtures; record actual ranges. Heuristics are not empirical calibration.
2. [x] Answer/boundary integrity (local): reproduce wrong-tool failure; fallback returns original requested facts; zero-length windows empty; health distinguishes configured mode from verified connectivity; direct shooting/causal bilingual questions handled conservatively. Run regression and full suites.
3. [ ] Meaningful explainer (local preparation, Azure verification blocked): calculated packet includes viewer clock, durations, player contributions, comparisons, source IDs and caveats. One model generates relevant interpretation; validate claims and abstain on unsupported requests. Declare compatible SDK dependencies, reuse client, bound total work. Live smoke trace must record deployment/model, latency, usage and fallback; no connectivity claim before success.
4. [ ] Held-out evaluation (depends on 3): identical questions/seeds for template, one-model and specialist policies; manual support/relevance/abstention rubrics plus measured latency/token usage and dated pricing-based cost. Never replace unavailable measurements with scripted scores. Prefer simplest policy meeting quality gates: no unsupported published factual claims in reviewed sample, relevant answers >=90%, unsupported-request abstention >=95%; provisional gates, not population guarantees.
5. [ ] Serving/revisions (local): same-origin production assets/API, reproducible startup; duplicate/revised events must recompute state/alerts/recaps through serving before ingestion claims. Smoke test built frontend with backend; model endpoint exposure requires bounded requests/access controls.
6. [ ] Submission (account/target dependent): confirm registration/category, public GitHub destination, judge-access build, rights/license, English README/architecture, public video <120 seconds. Verify from clean checkout and independent browser; preserve local fallback. Publication needs account access and destination.

## Blockers and scope

Registration confirmed by the user October 21. Azure account/resource creation is in progress; project/model deployment and authenticated local access remain unavailable. Do not request secrets. GitHub owner/destination and deployment access remain unknown. Do not add tracking, OCR, extra agents, Service Bus or database infrastructure merely for prize labels.

Verification commands: README local setup; `backend/.venv/Scripts/python.exe -m pytest backend/tests -q`; `backend/.venv/Scripts/ruff.exe check backend`; frontend `npm test -- --reporter=dot` and `npm run build`. Record completed evidence below, not inferred integration success.

## Completed local milestones (October 21)

- Data: sampling and position distributions corrected, fixtures regenerated. Seeds 0–19: completion 0.8319–0.8904; max goalkeeper shots/90 0.03927. Both teams observed in every sparse seed. `data-validation.json` records results. Ground truth remains reproducible via same-seed null fixture. Not empirically calibrated.
- Answer integrity: requested-answer timeout fallback, zero-duration windows, causal/shooting bilingual routing and configured-vs-unverified health status covered by regressions. Existing numerical percentile implementation retained.
- AI preparation: declared/locked optional SDK, locally installed. Experimental single-call context/interpretation path and paired evaluation runner implemented with scripted regression coverage. No live Foundry trace or semantic quality claim. Default specialist remains experimental; no architecture winner selected.
- Serving preparation: optional built-frontend mounting supports same-origin local judge build; API and asset routing covered. Public hosting/authentication remains incomplete.
- Remaining local work: event revisions through serving, public model access limits, complete provider usage accounting/client lifecycle optimization, comprehensive final holdout, independent browser test/video and submission assets. Account-dependent: live model smoke/evaluation, public destination/deployment, judge access verification.


October 21 live verification update: tenant-specific authentication succeeded against the supplied Foundry project. Two gpt-4.1-mini Responses calls returned model output and token usage. Neither candidate passed structural output validation; the first introduced unsupported numeric tokens (89 and 100). Fallback remained active. See `docs/foundry-verification.json` (or `foundry-verification.json` from this directory). Earlier statements of no live requests are historical; a passing interpretation, semantic quality and reliability remain unverified. Next: retain rejected candidate diagnostics, repair output-contract adherence, then paired live evaluation. Do not widen validators merely to obtain a passing demo.


Latest milestone: 47 backend / 15 frontend tests, build/lint/format pass. Revision store is now connected to serving; see build ledger for verified correction behavior and remaining stale-display limitation. Actual Foundry connectivity/initial development evaluation is recorded, but semantic quality gates failed inspection. Current-policy refresh is blocked on completing another Microsoft sign-in. Public repository owner/destination, licensing choice, hosting/access and video remain outstanding.
