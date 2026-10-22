# MatchLens edited screenshot walkthrough — 105 seconds

The completed local file `artifacts/matchlens-walkthrough.mp4` is a silent, captioned **edited screenshot walkthrough**, not a continuous recording of interaction. It uses actual local-app captures `artifacts/demo-frames/01-overview.png` through `07-watch.png`, with readable regional crops. Persistent labels identify edited screenshots, synthetic data and template mode. Public upload/access verification remains separate.

The H.264 MP4 is 1920×1080 at 24 fps, exactly 105 seconds, with fast-start metadata. Its actual sequence is: 0–15s overview; 15–30s comparison; 30–45s key moments; 45–60s English count answer; 60–75s Spanish answer; 75–90s recap; 90–105s Watch companion. Counts, answers and recap are template outputs; no live model quality claim is made. The final caption identifies the SVG scene as illustrative, without footage recognition or tracking, and states that experimental AI quality remains unaccepted.

Reproduction: `backend/.venv/Scripts/python.exe artifacts/make_walkthrough.py` uses the locally installed `imageio-ffmpeg` utility's bundled FFmpeg and Windows Segoe UI fonts. Source screenshots, video, script and `artifacts/matchlens-walkthrough-captions.json` are ignored local artifacts; explicitly include them for delivery. `--evidence artifacts/matchlens-walkthrough.mp4` can attach the reviewed video to a judge ZIP. Intermediates/sample frames are in `artifacts/video-build/`. Decoded metadata verifies 105.0 seconds and 1920×1080; sampled frames from all seven sections were visually inspected for disclosure, crop relevance and readability.

The optional live-recording narration below remains a separate rehearsal plan; it does not describe the edited video's exact cuts or imply recorded continuous interaction.

| Time | Screen action | Spoken narration |
| --- | --- | --- |
| 0–12s | Show the full Explore workspace and clock. | “MatchLens helps a football viewer inspect what changed and who appears in the recorded actions. This demonstration uses fictional, synthetic match data.” |
| 12–30s | Point to comparison windows and entry routes. | “Statistics are computed deterministically from events at the selected clock. Here we compare entries and routes around the anchor. Window durations and small samples matter; these are observations, not proof that a substitution caused a change.” |
| 30–47s | Select a player, then open Key moments and one supporting sequence. | “Select a player to inspect recorded involvement and the events behind a key moment. Match counts are separate from these illustrative season percentiles, which use eligible fictional peers.” |
| 47–64s | Ask “How many passes has this player completed?” with the player selected. Show answer and evidence. | “The answer uses the same clock-limited facts and supporting event IDs. This output is labeled as a deterministic template. Unsupported tracking or causal claims are outside the available evidence.” |
| 64–80s | Seek back; request a new recap at that clock. | “Seeking changes the facts available to analysis. A newly requested recap summarizes only the selected point in the replay, so viewers can explore without reading future events.” |
| 80–91s | Switch Watch/Explore and point to the scene. | “Watch adds an illustrative scene and compact action map. The scene is generated from events; this is not video recognition or real tracking.” |
| 91–105s | Return to main workspace; optionally show the judge guide beside it. | “The local demo works without cloud credentials. Foundry calls have been verified, but experimental interpretations failed semantic checks and are not presented as reliable. The source package includes setup, verification evidence and clear limitations.” |

Keep cuts within the 105-second budget; omit waiting, typing and loading time. If the wording of the count question routes differently in the final build, use a rehearsed passing-count question and retain the displayed provenance label. Do not narrate exact counts before seeing the final clock/scenario. Do not claim a completed live feed, hosted deployment, real footage or accepted model quality.
