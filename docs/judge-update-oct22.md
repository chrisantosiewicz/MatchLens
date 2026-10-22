# MatchLens update — October22 location/editorial revision

Demo: https://matchlens-chris-demo-2026.azurewebsites.net
Evidence: https://matchlens-chris-demo-2026.azurewebsites.net/evidence/index.html
Source: https://github.com/chrisantosiewicz/MatchLens

The prototype now explains where a player's action occurred and its recorded role in a sequence: pass origin/destination/distance, last/second-last/third-last completed pass before a shot, actual turnover actor, intervening actions, and recovery-to-entry/shot. Backward circulation is described without claiming intent to manage tempo. Defensive lines, pressure, nearby support and receiver control error remain unobserved.

Editorial rules are deterministic and versioned. Player/team contrasts use box entries on both sides, full exposure and nontrivial activity gates. Completed entry possessions are counted once; unfinished groups are excluded. Sparse feeds suppress absence/trend/game-state conclusions. Replacement/listed position and active minutes are shown without assuming tactical equivalence or attributing substitution effects. Fan and analyst retain identical conclusions and limitations. Starting thresholds are editorial policies, not validated benchmarks.

Verification:84backend regressions,23frontend tests, lint/build/package checks; anonymous deployment checks recorded separately. Core remains synthetic and selected-clock safe, with revision invalidation and source-complete local fallback.

AI caveat: v8/v9 generated structurally valid but semantically problematic prose. Retained raw candidates and review notes identify subject, metric, exposure and attribution issues. Current additional guards return fallback when replaying saved v9 candidates offline, with0new model calls. The evidence viewer distinguishes that replay from original generation. No independent human semantic acceptance, calibrated football accuracy or uptime guarantee is claimed. Public production remains templates without paid calls.

Current source of truth:STATUS.md. Applied owner/editorial rules:docs/football-meaning-review.md. Video quality work remains deferred; final rights/category/eligibility/submission decisions remain with owner.
