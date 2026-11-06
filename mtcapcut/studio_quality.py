"""Final long-form editorial invariants, independent of the provider repair path."""

from collections import Counter, defaultdict
from typing import Iterable


MAX_REUSED_SOURCE_US = 500_000


def longform_diversity_report(candidate: dict) -> dict:
    """Measure still reuse and source-time reuse in the final candidate."""
    visuals = [item for item in candidate.get("segments", [])
               if item.get("kind") in {"picture", "video"}]
    pictures = [item["asset_id"] for item in visuals if item["kind"] == "picture"]
    repeated_pictures = sorted(asset_id for asset_id, count in Counter(pictures).items() if count > 1)
    video_ranges = defaultdict(list)
    for item in visuals:
        if item["kind"] == "video":
            start = item["source_start_us"]
            video_ranges[item["asset_id"]].append((start, start + item["duration_us"]))
    reused_source_us = 0
    largest_pair_overlap_us = 0
    for ranges in video_ranges.values():
        ranges.sort()
        for index, (start, end) in enumerate(ranges):
            for prior_start, prior_end in ranges[:index]:
                largest_pair_overlap_us = max(
                    largest_pair_overlap_us, max(0, min(end, prior_end) - max(start, prior_start)))
        total = sum(end - start for start, end in ranges)
        merged = []
        for start, end in ranges:
            if not merged or start > merged[-1][1]:
                merged.append([start, end])
            else:
                merged[-1][1] = max(merged[-1][1], end)
        reused_source_us += total - sum(end - start for start, end in merged)
    return {
        "visual_shots": len(visuals),
        "picture_shots": len(pictures),
        "unique_picture_assets": len(set(pictures)),
        "video_shots": sum(len(ranges) for ranges in video_ranges.values()),
        "repeated_picture_asset_ids": repeated_pictures,
        "reused_video_source_us": reused_source_us,
        "largest_pair_overlap_us": largest_pair_overlap_us,
    }


def validate_longform_diversity(candidate: dict) -> dict:
    report = longform_diversity_report(candidate)
    if report["repeated_picture_asset_ids"]:
        raise ValueError("long-form candidate repeats picture assets")
    if (report["reused_video_source_us"] > MAX_REUSED_SOURCE_US
            or report["largest_pair_overlap_us"] > MAX_REUSED_SOURCE_US):
        raise ValueError("long-form candidate reuses video source time")
    return report


def visual_evidence_report(candidate: dict, observations: Iterable[dict]) -> dict:
    """Report what part of selected source time was actually visually observed.

    A sampled frame is a point observation, not evidence for the whole shot.
    This metric reports coverage; it does not grade artistic quality.
    """
    visual_by_asset = defaultdict(list)
    for row in observations:
        if row.get("modality") in {"vision", "ocr"}:
            visual_by_asset[row.get("asset_id")].append(row)
    shots = []
    selected_video_us = observed_video_us = 0
    for segment in candidate.get("segments", []):
        kind = segment.get("kind")
        if kind not in {"video", "picture"}:
            continue
        asset_id = segment.get("asset_id")
        start = int(segment.get("source_start_us", 0))
        duration = int(segment["duration_us"])
        end = start + duration
        intervals = []
        samples = 0
        for row in visual_by_asset.get(asset_id, []):
            row_start, row_end = row.get("start_us"), row.get("end_us")
            if row_start is None:
                if kind == "picture":
                    samples += 1
                continue
            if row_end is not None and row_start < end and row_end > start:
                samples += 1
                intervals.append((max(start, row_start), min(end, row_end)))
        observed = 0
        if kind == "video":
            selected_video_us += duration
            merged = []
            for left, right in sorted(intervals):
                if merged and left <= merged[-1][1]:
                    merged[-1][1] = max(merged[-1][1], right)
                else:
                    merged.append([left, right])
            observed = sum(right - left for left, right in merged)
            observed_video_us += observed
            status = "unknown" if samples == 0 else (
                "observed_interval" if observed >= duration else "sampled_only")
        else:
            status = "observed_still" if samples else "unknown"
        shots.append({"segment_id": segment.get("segment_id"), "asset_id": asset_id,
                      "kind": kind, "status": status, "visual_observation_count": samples,
                      "selected_source_us": duration if kind == "video" else None,
                      "observed_source_us": observed if kind == "video" else None})
    return {"shots": shots, "selected_video_source_us": selected_video_us,
            "observed_video_source_us": observed_video_us,
            "video_observed_fraction": (observed_video_us / selected_video_us
                                        if selected_video_us else None),
            "sampled_only_shot_count": sum(row["status"] == "sampled_only" for row in shots),
            "unknown_shot_count": sum(row["status"] == "unknown" for row in shots)}
