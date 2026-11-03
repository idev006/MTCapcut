"""Provider-neutral shot candidates and deterministic frame sampling."""

from dataclasses import dataclass
from pathlib import Path

from .config import ShotAnalysisSettings


@dataclass(frozen=True)
class ShotCandidate:
    start_us: int
    end_us: int
    boundary_score: float | None


@dataclass(frozen=True)
class FrameSample:
    shot_index: int
    at_us: int


class SceneDetectShotEngine:
    producer_version = "scenedetect-0.7.2"

    def __init__(self, settings: ShotAnalysisSettings):
        if not settings.enabled:
            raise ValueError("shot analysis is disabled")
        self.settings = settings

    def detect(self, source: Path) -> list[ShotCandidate]:
        if not source.is_file():
            raise FileNotFoundError(source)
        from scenedetect import SceneManager, StatsManager, open_video
        from scenedetect.detectors import ContentDetector

        stats = StatsManager()
        manager = SceneManager(stats_manager=stats)
        manager.add_detector(ContentDetector(
            threshold=self.settings.threshold,
            min_scene_len=self.settings.min_scene_len_frames,
        ))
        video = open_video(str(source))
        manager.detect_scenes(video=video, show_progress=False)
        scenes = manager.get_scene_list(start_in_scene=True)
        output = []
        for index, (start, end) in enumerate(scenes):
            start_us = round(float(start.seconds) * 1_000_000)
            end_us = round(float(end.seconds) * 1_000_000)
            if end_us <= start_us:
                continue
            score = None
            if index:
                value = stats.get_metrics(start.frame_num, [ContentDetector.FRAME_SCORE_KEY])[0]
                score = float(value) if value is not None else None
            output.append(ShotCandidate(start_us, end_us, score))
        if not output:
            raise RuntimeError("shot detector produced no source ranges")
        for previous, current in zip(output, output[1:]):
            if current.start_us != previous.end_us:
                raise RuntimeError("shot detector produced a non-contiguous map")
        return output


def sample_times(shots: list[ShotCandidate], frames_per_shot: int) -> list[FrameSample]:
    if frames_per_shot < 1:
        raise ValueError("frames_per_shot must be positive")
    samples = []
    for shot_index, shot in enumerate(shots):
        if shot.end_us <= shot.start_us:
            raise ValueError("shot range must be positive")
        duration = shot.end_us - shot.start_us
        positions = {
            min(shot.end_us - 1, shot.start_us + round(duration * (index + 1) / (frames_per_shot + 1)))
            for index in range(frames_per_shot)
        }
        samples.extend(FrameSample(shot_index, at_us) for at_us in sorted(positions))
    return samples
