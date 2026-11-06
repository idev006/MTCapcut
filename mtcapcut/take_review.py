"""Conservative, provider-neutral take-cleanup suggestions.

Original MTCapcut implementation informed by a review of AutoVideoMaker
(https://github.com/bonciarello/AutoVideoMaker). No upstream code copied.
Candidates are review-only: never mutate media or a CapCut project.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
import unicodedata

from .map import UnderstandingMap


@dataclass(frozen=True)
class WordToken:
    text: str
    start_us: int
    end_us: int
    confidence: float = 1.0
    observation_id: str | None = None


@dataclass(frozen=True)
class TakeSuggestion:
    kind: str
    start_us: int
    end_us: int
    reason: str
    review_required: bool = True
    asset_id: str | None = None
    evidence_ids: tuple[str, ...] = ()


def _normal(text: str) -> str:
    return "".join(
        ch for ch in unicodedata.normalize("NFKC", text).casefold()
        if unicodedata.category(ch)[0] in {"L", "N"}
    )


def suggest_take_cleanup(
    words: list[WordToken],
    *,
    minimum_pause_us: int = 700_000,
    maximum_repeat_gap_us: int = 400_000,
    minimum_confidence: float = 0.75,
) -> tuple[TakeSuggestion, ...]:
    """Find audible pauses and immediate word repeats, without auto-deleting.

    Word-level timestamps are mandatory. Silence derived from word gaps is
    *not* proof of acoustic silence; candidates require human review.
    """
    if minimum_pause_us < 0 or maximum_repeat_gap_us < 0:
        raise ValueError("gap thresholds must be nonnegative")
    if not 0 <= minimum_confidence <= 1:
        raise ValueError("minimum_confidence must be in [0, 1]")
    previous_end = 0
    for i, word in enumerate(words):
        if word.start_us < 0 or word.end_us <= word.start_us:
            raise ValueError(f"invalid timestamp at word {i}")
        if not 0 <= word.confidence <= 1:
            raise ValueError(f"invalid confidence at word {i}")
        if i and word.start_us < previous_end:
            raise ValueError("overlapping or unsorted word timestamps")
        previous_end = word.end_us

    findings: list[TakeSuggestion] = []
    for left, right in zip(words, words[1:]):
        gap = right.start_us - left.end_us
        if gap >= minimum_pause_us and gap > 0:
            findings.append(TakeSuggestion(
                "possible_pause", left.end_us, right.start_us,
                "Gap between ASR words; verify audio before removing",
                evidence_ids=tuple(item for item in (left.observation_id, right.observation_id) if item),
            ))
        ltext, rtext = _normal(left.text), _normal(right.text)
        if (ltext and ltext == rtext
                and 0 <= gap <= maximum_repeat_gap_us
                and left.confidence >= minimum_confidence
                and right.confidence >= minimum_confidence):
            findings.append(TakeSuggestion(
                "possible_repetition", left.start_us, left.end_us,
                "Adjacent identical ASR words; may be deliberate emphasis",
                evidence_ids=tuple(item for item in (left.observation_id, right.observation_id) if item),
            ))
    return tuple(sorted(findings, key=lambda f: (f.start_us, f.end_us, f.kind)))


def suggest_for_asset(understanding: UnderstandingMap, asset_id: str) -> tuple[TakeSuggestion, ...]:
    """Read only current-version word evidence; never alter media or the timeline."""
    understanding.get_asset(asset_id)
    observations = [row for row in understanding.current_asset_timeline(asset_id)
                    if row["modality"] == "speech_word"]
    if not observations:
        return ()
    words = [WordToken(row["text"], row["start_us"], row["end_us"],
                      row["confidence"] if row["confidence"] is not None else 0.0,
                      row["observation_id"])
             for row in sorted(observations, key=lambda row: (row["start_us"], row["end_us"]))]
    return tuple(replace(item, asset_id=asset_id) for item in suggest_take_cleanup(words))
