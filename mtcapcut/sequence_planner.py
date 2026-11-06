"""Stable, bounded sequence jobs for provider-authored long-form edits."""

from dataclasses import dataclass


MAX_SEQUENCE_US = 30_000_000
MIN_PREFERRED_SEQUENCE_US = 12_000_000


@dataclass(frozen=True)
class SequenceJob:
    sequence_id: str
    index: int
    start_us: int
    duration_us: int
    story_beat: str


def plan_sequence_jobs(duration_us: int, story_beats: tuple[str, ...] | list[str],
                       *, max_duration_us: int = MAX_SEQUENCE_US) -> tuple[SequenceJob, ...]:
    """Partition exact runtime; spread supplied beats across bounded jobs."""
    if duration_us <= 0 or max_duration_us < MIN_PREFERRED_SEQUENCE_US:
        raise ValueError("invalid long-form sequence duration")
    beats = tuple(beat.strip() for beat in story_beats if beat.strip())
    if not beats:
        raise ValueError("long-form planning requires story beats")
    minimum_count = (duration_us + max_duration_us - 1) // max_duration_us
    preferred_count = min(len(beats), max(1, duration_us // MIN_PREFERRED_SEQUENCE_US))
    count = max(3 if duration_us >= 90_000_000 else 1,
                minimum_count, preferred_count)
    base, remainder = divmod(duration_us, count)
    jobs = []
    cursor = 0
    for index in range(count):
        length = base + (1 if index < remainder else 0)
        beat = beats[min(len(beats) - 1, index * len(beats) // count)]
        jobs.append(SequenceJob(f"seq{index + 1:04d}", index + 1, cursor, length, beat))
        cursor += length
    return tuple(jobs)
