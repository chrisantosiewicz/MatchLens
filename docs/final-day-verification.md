# October 27 final-day verification

This record describes local verification after the positional-source identity fix. Earlier Foundry traces remain historical source freezes; no new remote model calls were made.

## Confirmed bug and fix

During browser recording, ordinary player questions on the corner fixture returned HTTP 500 (`mixed_source_revision`). API revisions included explicit position frames, while the explanation context used an events-only hash. The new shared `matchlens.provenance.source_version` helper preserves the existing API hash input and includes the same revision-bound positional content in both paths.

The regression failed before the fix and passed afterward. It exercises passing, involvement and causality questions plus viewing guidance on the positional fixture. Separate static code review found no consequential issue and confirmed byte-compatible hashing and position-correction sensitivity. This is engineering review, not independent football or user evaluation.

## Checks

- Backend: **140 passed in 8.32 seconds** using `backend/.venv/Scripts/python.exe -m pytest backend/tests --basetemp artifacts/pytest-final-oct27-release -q`.
- Frontend: **35 passed across eight files** using `npm test -- --reporter=dot`.
- Ruff: `backend/.venv/Scripts/ruff.exe check backend` passed.
- Production build: `npm run build` passed; CSS `index-CZLXnIdM.css`, JavaScript `index-BshXw9bG.js`.
- Packaging regression: **1 passed** using `backend/.venv/Scripts/python.exe -m pytest scripts/test_package_judge.py -q`.
- `git diff --check` passed, with Windows line-ending notices only.

An initial sandbox frontend run could not rename temporary transform files and ran no tests. It was rerun successfully with normal local permissions. A sandbox backend rerun stalled and was stopped; the separate normal-permission run above completed. These infrastructure failures are not counted as passing runs.

## Browser and video evidence

The corrected local server returned a clock-stamped causal guard instead of HTTP 500. English and Spanish recaps were generated at 70:00. Captures also show the passing sequence, corner setup/delivery and event IDs, recorded correction withdrawal, and historical Foundry guide selection.

`matchlens-final-demo-oct27.mp4`: 1920×1080, 115.94 seconds, 4,177,932 bytes; SHA-256 `664ce7d60544cf045fe5f00edf790c4f97ab48888e7e946e86697c78ac49af98`. English synthesized narration; edited browser UI capture with held states and sampled clock playback, not continuous native screen recording. Full-file decoding and representative-frame inspection passed. Video quality acceptance by the owner, accepted-host publication and anonymous playback remain pending.

## Boundaries

Azure deployment remains on hold at the owner's request. The public app remains the older October 22 template build. Local corner functionality is deterministic, based on explicitly synthetic snapshots, and does not establish player intent or continuous tracking. Independent viewer evaluations remain zero; no model superiority, viewer benefit, new reliability result or competition submission is claimed.
