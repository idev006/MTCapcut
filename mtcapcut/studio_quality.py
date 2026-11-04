"""Final long-form editorial invariants, independent of the provider repair path."""

from collections import Counter, defaultdict


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
