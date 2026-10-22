# Held-out explanation evaluation

Run `python -m matchlens.evaluate` with the backend environment from the repository root. The runner uses seeds 101/202, not the showcased seed 7: a shift and a sparse scenario, a midfielder and a recently introduced substitute, ten bilingual questions each. The same cases go to template, single-call interpretation and canonical specialist policies. Model policies retain the same pre-routing for unsupported requests. This is a small development evaluation, not an unbiased final benchmark; reserve new seeds/questions for final acceptance after tuning.

Offline output: 20 completed template rows and 40 explicit skipped live-policy rows. No model quality, cost or latency is inferred from skips. Scripted tests exercise control flow only.

With authenticated Foundry configuration, `--live` makes billable model requests. Save the JSON alongside the tested commit, SDK lock, deployment name, model/version, date and scenario seed. Single-call answer usage is recorded when supplied by the provider; all specialist calls now record usage and latency when supplied by the provider. Do not compare cost until every call's input/output tokens and deployment-specific dated prices are recorded. Cost remains null, not zero, until calculated from that evidence. Transport timeout is not an end-to-end latency SLA.

Review outputs blind to policy where possible. Fill factual_support (every factual claim supported by cited source and correct subject/time), relevance (directly answers the question), appropriate_abstention (unsupported questions refused without implying off-ball/causal knowledge), each as pass/fail with a reviewer note. Verify citations contain supporting events, not merely valid IDs. Check English/Spanish meaning with an actual bilingual reviewer. Report denominators, disagreements, failures and exact sample size.

Provisional acceptance gates: no unsupported factual claims in the reviewed sample, >=90% relevance and >=95% appropriate abstention. A tiny passing sample does not establish population reliability. Compare latency distributions only for completed live calls; include failures and fallback frequency. Keep the simplest policy meeting quality needs. No winner is selected yet: initial live comparisons did not meet semantic acceptance; a current-contract rerun requires renewed authentication.


## October 21 measured development run

`evaluation-results.json` records the initial 60-row comparison: 45 model calls, 45,309 input tokens and 1,839 output tokens. Raw single-model policy: 12 calls; specialist: 33 calls. Median request latencies among model-attempt cases were approximately 1.74s and 3.00s respectively; first authentication is included and this is not a service SLA. The initial comparison has a conditional USD 0.021066 Global Standard retail estimate, using official dated meters in price-reference.json. Actual deployment SKU, Azure bill, credits and other resource charges remain unverified.

Developer inspection found incorrect time-window wording, unsupported tactical language and poor direct-count relevance in candidate interpretations. Do not treat structural acceptance as factual support. Existing sentence-selection specialists did not establish an improvement over deterministic answers. No policy met the proposed semantic-quality gates in this inspection; no independent bilingual human evaluation occurred.

Review caught a measurement mismatch after the application switched to hybrid routing: the initial raw single-model experiment sent count questions to a model while the application bypassed them. The runner now shares `interpretation_requested` with the API and has regression coverage. Initial figures are historical raw-policy measurements, not measurements of the current deployed hybrid. A refreshed current-policy live run and fresh-seed acceptance remain pending sign-in; do not relabel old traces as new results.

Current choice: deterministic counts and unsupported-question boundaries by default, one optional experimental model interpretation for why/change questions. The specialist remains opt-in for comparison, not a recommended production default. This favors simpler orchestration without claiming the model is reliable yet.

Current rate contract supplies exact window durations, calculated per-minute team rates and player active minutes. Structured fields must match the calculated comparison direction. This prevents one class of error but does not prove free-form claims: final acceptance still requires manual subject/window/evidence review. Signed numeric values are validated without dropping minus signs.

## October 21 current-contract rerun

After renewed sign-in, all 60 paired rows completed on commit d814db3. See evaluation-current-results.json. The hybrid single policy made 6 calls (4 structural acceptances, 1 abstention, 1 fallback); specialist made 40 calls. Developer inspection still rejected semantic quality: action-rate/pass wording, area-presence inference, internal-key leakage, and specialist relevance errors. Conditional retail estimates are recorded, not actual bills. Follow-up fixes distinguish hyphenated minute ranges from negative values and tighten wording instructions. Those follow-up instructions require fresh live acceptance; a passing regression is not a passing model evaluation.
