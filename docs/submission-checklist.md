# Submission checklist — October 27, 2026

Current implementation status: [STATUS.md](../STATUS.md). Submission copy: [submission-pitch.md](submission-pitch.md). Recording plan: [demo-script.md](demo-script.md).

**Owner review at 11:30 PM: use [the final 30-minute review packet](FINAL-REVIEW.md).** The replacement video is [uploaded privately](https://youtu.be/9Jr04kSZD5w); owner playback started. Make it public only after owner approval, then verify signed-out access. The current source/test ZIP was published and its GitHub asset digest matches the local archive; the 237 extracted payload hashes and ordinary question/guide smoke checks passed. Dependencies were reused for extraction smoke, not installed from scratch.

## Verified evidence and boundaries

- Local corner extension: complete 22-player synthetic frames, four phases, selected-clock occupancy and endpoint movement, English/Spanish answers and recaps. See [corner context](corner-context.md) and [local evidence](evaluations/corner-context-local.json).
- October 27 checks after the source-identity fix: **140 backend tests, 35 frontend tests, Ruff, production build and one packaging regression passed**. Commands and infrastructure caveats are in [final verification](final-day-verification.md). The fix prevents ordinary questions and viewing guidance from failing on positional fixtures.
- Actual authenticated Microsoft Foundry `gpt-4.1-mini` execution is retained in [viewing-guide evidence](evaluations/viewing-guide-v1.json): eight calls, comprising one analyst and seven guide calls. Seven guide selections passed catalog validation. This measures execution/selection validity, not interpretation quality or viewer benefit.
- Independent human evaluations: **0**. [Owner editorial review](owner-editorial-review-2026-10-25.md) is owner feedback, not independent acceptance. Earlier proposed non-corner cutbacks/transitions remain unimplemented.
- Public application is the older October 22 guide build in template mode. The local corner extension has not been publicly deployed. **Keep Azure deployment on hold: “Keep it local for now.”** No anonymous paid-model calls are enabled.
- Replacement `artifacts/matchlens-final-demo-oct27.mp4` rendered at **1920×1080, 115.94 seconds**, with English synthesized narration and readable captions. It is explicitly an edited browser UI capture with held states, not continuous native screen recording. Full decoding and representative-frame inspection passed; owner quality review, public upload and anonymous playback remain pending. The prior 105-second silent walkthrough is historical.

## Remaining submission actions

1. Review the completed, privately uploaded replacement recording. Make the approved video public and test anonymous playback. A private video is not the required public video URL.
2. Preserve the verified product handoff at commit 802f154 and its published package. Newer documentation-only commits do not change that evaluated product source. Keep the private organizer key, credentials, local environment files and account/session artifacts excluded from public materials.
3. Verify the public GitHub URL and the exact delivered source revision. Recheck anonymous judge access to the older public demo; explicitly identify its version. Supply a working local test build and English setup instructions for the corner extension while deployment remains on hold. Confirm the selected delivery satisfies the organizer's access requirement through November 10.
4. Owner confirms category (recommendation: **Best Use of Microsoft Foundry**, choice unconfirmed), eligibility, rights, asset provenance and code license. [Provenance](provenance.md) records that no project code license has been selected.
5. Owner completes the final platform fields with reviewed description, source/demo/video links and Azure contribution. Confirm submission receipt. Registration alone is not final submission.

The [official rules](https://github.com/microsoft/insidethegamehackathon/blob/main/OFFICIAL%20RULES.md), checked October 27, require a public GitHub repository and a public working-project video under two minutes (§4.4), a free working website/demo or test build available through November 10 (§4.8), and English submission materials (§4.9). Deadline: **October 27, 11:59 PM PDT = October 28, 1:59 AM Chicago time**. These notes do not certify eligibility or compliance.

## Reproduce verification and package

From the repository root in PowerShell, with dependencies installed as described in [judge-guide.md](judge-guide.md):

```powershell
New-Item -ItemType Directory -Force artifacts | Out-Null
backend/.venv/Scripts/python.exe -m pytest backend/tests --basetemp artifacts/pytest-final-oct27 -q
backend/.venv/Scripts/ruff.exe check backend
Push-Location frontend
npm test -- --reporter=dot
npm run build
Pop-Location
backend/.venv/Scripts/python.exe scripts/package_judge.py --output artifacts/matchlens-judge-final-oct27.zip
```

The output path must not already exist. The packager uses eligible Git-tracked working-tree files; ensure new submission documents are included before packaging. Only after reviewing a completed video, add `--evidence artifacts/matchlens-final-demo-oct27.mp4` if the video should also be bundled. The archive does not publish the video or submit the project.
