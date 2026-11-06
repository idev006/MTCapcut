# AutoVideoMaker research transfer — 2026-11-06

## Source and boundary
Upstream: https://github.com/bonciarello/AutoVideoMaker
Inspected: README, src/cleanup_rules.py, src/intervals.py and repository file listing.
This research **does not import or copy upstream source**. No LICENSE file was
visible in the upstream repository root at inspection time: public source alone
does not grant reuse or redistribution rights. Confirm again before any vendoring.

## Findings
- Speech word timestamps drive edit boundaries; FFmpeg silence analysis is fallback.
- Candidate take-cleanup classes include false starts, repeated words, retakes
  and explicit verbal cues. Some candidates are uncertain and need review.
- Export constructs CapCut drafts and Premiere EDL; README documents manual
  compatibility verification with CapCut 9.4 on macOS. This does not establish
  Windows compatibility for the upstream draft builder.
- Cached words.json avoids repeated transcription expense.
- Its Italian-focused normalization and cue vocabulary must NOT be directly
  applied to Thai speech.
- Upstream is not an end-to-end B-roll understanding or world-class storytelling
  proof.

## Fit with MTCapcut SSOT
MTCapcut already has local faster-whisper, timestamped evidence, SQLite asset
understanding, approval gates, provider-neutral TimelinePlan, editorial receipts
and a pyCapCut adapter. Do not replace these foundations with upstream modules.

## Implemented in this branch
- `mtcapcut.take_review`: original, dependency-free word-level candidate finder
  for gaps and adjacent repetitions; microsecond timestamp contract.
- Findings are *review-only*, not approved deletions and never modify files.
- `tests/test_take_review.py`: isolated regression coverage.

## Next integration gates
1. Extend the existing FasterWhisperEar to persist verified word-level timings
   as evidence, without breaking segment-level observations. Test Thai ASR.
2. Map suggestions to EditorialRevision/Receipt and make editorial approval
   mandatory before any removal.
3. Compare word-gap versus genuine FFmpeg acoustic silence, preserve breaths,
   music and ambience. Never assume ASR gap equals silence.
4. Add case-based tests for Thai emphasis, repeated proper nouns, cue words,
   deliberate repetition and multiple speakers.
5. Integrate cut decisions into the current TimelinePlan and Windows pyCapCut
   compatibility suite, retaining non-destructive media references.
6. Benchmark on consented, rights-cleared 5–10 minute video clips using
   precision, recall, false deletion rate, processing time, and cost.
7. Keep cloud AI optional: send compact context/event evidence, not entire
   long-form raw footage by default.

## Verification / status
Code changes staged for review. Unit tests supplied but **not run against
the user's Windows environment**. No assertion of live CapCut export or
production-grade edit quality. Run `python -m unittest tests.test_take_review -v`
then the full project suite before merging.
