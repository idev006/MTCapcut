# Three-minute autonomous studio retest

Updated: 4 November 2026

## Objective and authorship boundary

The `road-report-001` brief requests an approximately three-minute private review clip. OpenRouter receives the SSOT asset metadata and semantic observations, then acts as the creative council, director, lead editor and finishing designer. Python enforces durations, evidence, media constraints and user-locked copy/music. Codex does not choose shots or transitions for the deliverable.

## Evidence from the first complete run

- Run `4d8be4ad-31bd-47af-ad83-ec6155adacc5` produced `workspace/road-report-001/editorial/autonomous-candidate-v16-3min.json` with status `candidate_ready`, brief compliance `pass`, 180 seconds, 39 visuals, one music bed and three required title placements.
- OpenRouter finishing and pyCapCut produced `workspace/road-report-001/drafts/MT_ROAD_REPORT_001_AUTONOMOUS_PRO_3MIN_V1`, with 39 visual treatments and six transition materials in the draft JSON.
- A copy was opened in CapCut 9.8.0.4189 on this machine. The editor displayed a 03:00 timeline with image, audio and text tracks. Opening the draft proves structural compatibility, but the transition/filter resources and final aesthetic quality are not yet verified by export and human review.
- Automated diversity audit found only 10 distinct visual assets among 39 shots, including 23 uses of the same 118-second source video. Several source ranges repeat. This is a creative quality defect despite contract compliance.

## Correction and current gate

`StudioRoleEngine.create_long_timeline` now supplies earlier media choices to each 30-second provider request. It detects repeated stills and overlapping video source intervals. For each collision it presents observed, unused alternatives to OpenRouter and accepts only a schema-validated provider choice. If correction fails, the run rejects the candidate rather than lowering the quality rule. V17 and V18 failed the first strict diversity gate. V19 stopped because the provider omitted the explicit music filename from the typed brief. The Brief Interpreter now preserves the user's literal quoted music-file lock deterministically.

V20 passed brief compliance at exactly 180 seconds with 34 visual shots, 15 distinct stills and 19 distinct video starts. A deeper interval audit found 49.7 seconds of overlap within 114 seconds of video usage. The gate now compares full source intervals, allows at most 0.5 second of pairwise overlap, and asks OpenRouter to select evidence-backed alternatives. V20 was rendered only for technical comparison; its overlap finding prevents creative acceptance.

V21 failed the central temporal evidence binder because one video source range had no overlapping machine observation. The long-form editor now checks temporal evidence while evaluating each sequence and routes such shots through the same provider-selected replacement path. V22 tested that correction.

V22 run `4deaab5f-05f4-4580-81ff-46bb4b63381e` passed: 180 seconds, 32 visual shots, 24 unique still images, eight video shots, only 0.1 second total video-source overlap, one required music asset and brief compliance `pass`. OpenRouter finishing selected six `Mix` transitions, 30 `Soft_Grain` filters, one `BW_2` filter, with text animation disabled for local compatibility. The pyCapCut draft is `workspace/road-report-001/drafts/MT_ROAD_REPORT_001_AUTONOMOUS_PRO_3MIN_V22`. CapCut 9.8 opened the draft and exported locally without a Pro-material block to `workspace/road-report-001/exports/road-report-001-studio-v22.mp4`. FFprobe confirmed H.264/AAC, 1920×1080, 30 fps, 180.001 seconds, 220,367,458 bytes. The export screen was closed without sharing.

CapCut 9.8 opened V16, but its Export action reported that `Swipe Left` transitions require Pro. The new finishing profile offers OpenRouter only transitions and filters whose pinned pyCapCut 0.0.4 metadata has `is_vip=false` (`Mix`/`Overlay`, `Soft_Grain`/`BW_2`). Existing old manifests remain readable; new finishing rejects Pro materials. V22 verified that the installed CapCut 9.8 exports this local-safe profile.

The 3-minute FFmpeg private preview from V16 is available at `workspace/road-report-001/exports/autonomous-v16-3min-preview.mp4`. FFprobe verified H.264/AAC, 1920×1080, exactly 180 seconds. Its renderer does not prove the CapCut transitions/filters. World-class creative quality remains unproven until a completed revised export receives blind human review against the brief.

Automated suite after the V22 export corrections: 118 tests pass. Later pipeline diagnosis and fixes are recorded in [doc/37](./37-v22-diagnosis-design-and-delivery-plan.md); V22 remains the pre-fix creative sample.
